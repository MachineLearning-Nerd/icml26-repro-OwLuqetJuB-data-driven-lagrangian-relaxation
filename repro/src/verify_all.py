"""Independent raw-evidence verifier and claim verdict renderer."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "outputs/claims_raw.json"
CLAIMS = ROOT / "repro/configs/live_claims.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log_slope(xs, ys) -> float:
    return float(np.polyfit(np.log(np.asarray(xs, float)), np.log(np.asarray(ys, float)), 1)[0])


def scalar_risk(values: np.ndarray, p: float) -> np.ndarray:
    low, high = 1.0, 2.0
    optimum = high if p > 0.5 else low
    def utility(x):
        return (1 - p) * np.minimum(x / 2, low - x / 2) + p * np.minimum(x / 2, high - x / 2)
    return utility(np.full_like(values, optimum)) - utility(values)


def independent_geometry(seed=7851, trials=2500) -> dict:
    rng = np.random.default_rng(seed)
    min_concavity = math.inf
    min_supergradient = math.inf
    max_norm_ratio = 0.0
    wrong_fail = 0
    max_fail = 0
    for _ in range(trials):
        s, d, m = 5, 4, 16
        a = rng.uniform(-1, 1, (s, d))
        b = rng.uniform(-1, 1, s)
        c = rng.normal(size=d)
        xs = rng.uniform(0, 1, (m, d))
        slopes = b[None, :] - xs @ a.T
        offsets = xs @ c
        p, q = rng.uniform(0, 2, (2, s))
        theta = rng.random()
        def minimum(pi):
            vals = offsets + slopes @ pi
            j = int(np.argmin(vals))
            return float(vals[j]), slopes[j]
        vp, gp = minimum(p)
        vq, _ = minimum(q)
        vm, _ = minimum(theta * p + (1 - theta) * q)
        min_concavity = min(min_concavity, vm - theta * vp - (1 - theta) * vq)
        min_supergradient = min(min_supergradient, vp + gp @ (q - p) - vq)
        bound = max(float(np.abs(b).max()), float(np.abs(xs @ a.T).max()))
        max_norm_ratio = max(max_norm_ratio, float(np.linalg.norm(gp) / (2 * bound * math.sqrt(s))))
        if vp + b @ (q - p) + 1e-10 < vq:
            wrong_fail += 1
        maxp, maxq = float((offsets + slopes @ p).max()), float((offsets + slopes @ q).max())
        maxm = float((offsets + slopes @ (theta * p + (1 - theta) * q)).max())
        if maxm + 1e-10 < theta * maxp + (1 - theta) * maxq:
            max_fail += 1
    return {
        "trials": trials,
        "min_concavity_margin": min_concavity,
        "min_supergradient_margin": min_supergradient,
        "max_norm_ratio": max_norm_ratio,
        "wrong_gradient_failures": wrong_fail,
        "max_control_failures": max_fail,
    }


def main() -> None:
    raw = json.loads(RAW.read_text())
    contract = json.loads(CLAIMS.read_text())
    require(raw["paper_id"] == contract["paper_id"] == "OwLuqetJuB", "paper ID mismatch")
    require(len(contract["claims"]) == 6, "live claim count changed")
    require(raw["source"]["all_pins_pass"], "recorded source pins failed")
    for row in raw["source"]["files"]:
        path = ROOT / row["path"]
        require(path.stat().st_size == row["bytes"], f"source size changed: {row['path']}")
        require(sha256(path) == row["expected"] == row["sha256"], f"source hash changed: {row['path']}")

    # Claim 1: recompute all raw ERM risks and the scaling law.
    erm_by_n: dict[int, list[float]] = {}
    for row in raw["claim_1_erm_raw"]:
        estimates = np.asarray(row["estimates"], float)
        recorded = np.asarray(row["scalar_excess"], float)
        rebuilt = scalar_risk(estimates, float(row["p_high"]))
        require(np.max(np.abs(recorded - rebuilt)) < 1e-14, "ERM raw risk mismatch")
        erm_by_n.setdefault(int(row["n"]), []).append(float(rebuilt.mean()))
    ns = sorted(erm_by_n)
    erm_means = [float(np.mean(erm_by_n[n])) for n in ns]
    erm_slope = log_slope(ns, erm_means)
    require(-0.65 < erm_slope < -0.35, f"ERM N slope outside sqrt law: {erm_slope}")
    require(all(r["normalized_by_s15_sqrt_n"] < 0.02 for r in raw["claim_1_erm_summary"]["rows"]), "ERM exceeds proof envelope")

    # Claims 2/4: rebuild every packing and Fano quantity from codewords.
    packing_by_s = {}
    for row in raw["claim_2_fano_packings"]:
        words = np.asarray(row["codewords"], np.uint8)
        distances = np.concatenate([np.count_nonzero(words[i + 1 :] != words[i], axis=1) for i in range(len(words) - 1)])
        require(len(words) == 2 ** (row["s"] // 8), "packing cardinality failure")
        require(int(distances.min()) >= row["s"] // 8, "packing separation failure")
        require(len(distances) == row["pair_count"], "packing pair count failure")
        packing_by_s[row["s"]] = (int(distances.min()), int(distances.max()), len(words))
    direct_by_s, warm_by_s = {}, {}
    for row in raw["claim_2_and_4_fano"]:
        s, n, eps = row["s"], row["n"], row["epsilon"]
        dmin, dmax, size = packing_by_s[s]
        exact_kl = n * dmax * eps * math.log((1 + eps) / (1 - eps))
        envelope = 4 * n * s * eps**2
        fano = 1 - (envelope + math.log(2)) / math.log(size)
        require(abs(exact_kl - row["exact_kl_max"]) < 1e-12, "exact KL mismatch")
        require(abs(envelope - row["paper_kl_envelope"]) < 1e-12, "KL envelope mismatch")
        require(exact_kl <= envelope and fano > 0.25, "invalid Fano certificate")
        direct = fano * eps * dmin / 4
        warm = fano * eps**2 * dmin / 4
        require(abs(direct - row["direct_risk_lower"]) < 1e-12, "direct lower mismatch")
        require(abs(warm - row["warm_risk_lower"]) < 1e-12, "warm lower mismatch")
        direct_by_s.setdefault(s, []).append(direct / (s / math.sqrt(n)))
        warm_by_s.setdefault(s, []).append(warm / (s / n))
    require(all(max(v) - min(v) < 1e-12 and min(v) > 0 for v in direct_by_s.values()), "direct minimax normalization drift")
    require(all(max(v) - min(v) < 1e-12 and min(v) > 0 for v in warm_by_s.values()), "warm minimax normalization drift")

    # Claim 3: recompute risk from every averaged iterate, then fit the rate.
    sga_by_n = {}
    for row in raw["claim_3_sga_raw"]:
        averaged = np.asarray(row["averaged_pi"], float)
        recorded = np.asarray(row["scalar_excess"], float)
        rebuilt = scalar_risk(averaged, float(row["p_high"]))
        require(np.max(np.abs(recorded - rebuilt)) < 1e-14, "SGA raw risk mismatch")
        sga_by_n.setdefault(row["n"], []).append(float(rebuilt.mean()))
    sga_ns = sorted(sga_by_n)
    sga_slope = log_slope(sga_ns, [np.mean(sga_by_n[n]) for n in sga_ns])
    require(-0.65 < sga_slope < -0.35, f"SGA N slope outside sqrt law: {sga_slope}")
    require(max(r["ratio"] for r in raw["claim_3_sga_summary"]["rows"]) < 1, "SGA theorem bound violated")

    # Claim 4: independently aggregate raw squared errors and compare exact risk.
    warm_by_n_raw = {}
    for row in raw["claim_4_warm_raw"]:
        values = np.asarray(row["scalar_squared_errors"], float)
        require(np.all(values >= 0) and np.all(np.isfinite(values)), "invalid warm raw errors")
        warm_by_n_raw.setdefault(row["n"], []).append(float(values.mean()))
    warm_ns = sorted(warm_by_n_raw)
    warm_means = [float(np.mean(warm_by_n_raw[n])) for n in warm_ns]
    warm_slope = log_slope(warm_ns, warm_means)
    require(-1.12 < warm_slope < -0.88, f"warm-start N slope outside 1/N law: {warm_slope}")
    require(max(r["relative_error"] for r in raw["claim_4_warm_summary"]["rows"]) < 0.03, "warm Monte Carlo/exact mismatch")
    typo = raw["claim_4_warm_summary"]["literal_typo_control"]
    require(not typo["valid_distribution"] and abs(typo["sum"] - 1.2) < 1e-15, "literal typo control did not fail")
    require(abs(typo["corrected_sum"] - 1) < 1e-15, "corrected distribution invalid")

    # Claim 5: integrate by a method independent of the producer's quadrature.
    t = np.linspace(0, 32, 300_001)
    unit_integral = float(np.trapezoid(np.sqrt(math.log(3) + t) * np.exp(-t), t))
    complexity_constants = []
    for row in raw["claim_1_and_5_complexity"]:
        s, n = row["s"], row["n"]
        require(abs(row["lipschitz"] - 2 * math.sqrt(s)) < 1e-12, "L mismatch")
        require(abs(row["diameter"] - 2 * math.sqrt(s)) < 1e-12, "D mismatch")
        independent_integral = row["radius"] * unit_integral
        require(abs(independent_integral - row["integral"]) / row["integral"] < 2e-8, "Dudley integration mismatch")
        require(row["integral"] <= row["paper_envelope"], "Dudley envelope failure")
        for cover in row["covering_rows"]:
            rebuilt = s * math.log(1 + 4 * s / cover["delta"])
            require(abs(rebuilt - cover["log_cover_bound"]) < 1e-12, "covering formula mismatch")
        complexity_constants.append(row["normalized_by_s15_sqrt_n"])
    require(max(complexity_constants) - min(complexity_constants) < 1e-12, "Rademacher scaling drift")

    # Claim 6: fresh finite-MILP enumeration, separate random stream and code path.
    geometry = independent_geometry()
    require(geometry["min_concavity_margin"] > -1e-11, "concavity failed")
    require(geometry["min_supergradient_margin"] > -1e-11, "supergradient failed")
    require(geometry["max_norm_ratio"] <= 1 + 1e-12, "norm bound failed")
    require(geometry["wrong_gradient_failures"] > 0, "wrong-gradient control survived")
    require(geometry["max_control_failures"] > 0, "max-affine control survived")
    require(raw["claim_6_geometry"]["tight_norm_ratio"] == 1.0, "tight norm witness failed")
    require(raw["claim_6_geometry"]["missing_sqrt_s_control_ratio"] > 1, "missing-sqrt control survived")

    metrics = {
        "source_pins": True,
        "erm_n_slope": erm_slope,
        "packing_pairs": sum(row["pair_count"] for row in raw["claim_2_fano_packings"]),
        "min_fano_error": min(row["fano_error_lower"] for row in raw["claim_2_and_4_fano"]),
        "sga_n_slope": sga_slope,
        "max_sga_bound_ratio": max(r["ratio"] for r in raw["claim_3_sga_summary"]["rows"]),
        "warm_n_slope": warm_slope,
        "max_warm_exact_relative_error": max(r["relative_error"] for r in raw["claim_4_warm_summary"]["rows"]),
        "rademacher_normalized_constant": complexity_constants[0],
        "producer_geometry_trials": raw["claim_6_geometry"]["trials"],
        "independent_geometry": geometry,
    }
    evidence = [
        "ERM raw trials and an independent risk reconstruction support the O(s^1.5/sqrt(N)) upper envelope; observed N slope is %.6f." % erm_slope,
        "%d pairwise Hamming checks, exact Bernoulli KL, and positive Fano factors certify an Omega(s/sqrt(N)) hard family." % metrics["packing_pairs"],
        "Averaged SGA raw iterates independently reconstruct with N slope %.6f and maximum theorem-bound ratio %.6f." % (sga_slope, metrics["max_sga_bound_ratio"]),
        "Warm-start empirical means match the exact s(1-epsilon^2)/(4N) risk with N slope %.6f; the malformed appendix probabilities fail, while the complementary repair gives the matching Omega(s/N) Fano family." % warm_slope,
        "The covering formula is exact on all grid cells; independent dense integration reproduces the Dudley constant %.12f and the s^1.5/sqrt(N) scaling." % metrics["rademacher_normalized_constant"],
        "%d producer and %d independent finite-MILP trials verify concavity, the supergradient inequality, and 2B sqrt(s); wrong-gradient, max-affine, and omitted-sqrt(s) controls fail." % (raw["claim_6_geometry"]["trials"], geometry["trials"]),
    ]
    qualifications = [None, None, None, "Verified after correcting the Appendix Theorem 6.2 v_k=0 probability sign; the literal printed pair sums to 1+epsilon and is not a distribution.", None, "The paper calls the concave supergradient a subgradient; the reproduction follows its stated convention."]
    verdicts = {
        "paper_id": "OwLuqetJuB",
        "live_claim_count": 6,
        "possible_points": 12,
        "substantive_outcomes": 6,
        "metrics": metrics,
        "claims": [
            {"claim_number": i + 1, "claim": claim, "verdict": "verified", "evidence": evidence[i], **({"qualification": qualifications[i]} if qualifications[i] else {})}
            for i, claim in enumerate(contract["claims"])
        ],
        "all_claims_complete": True,
    }
    verdict_path = ROOT / "outputs/claim_verdicts.json"
    verdict_path.write_text(json.dumps(verdicts, indent=2, sort_keys=True))

    bundle_paths = [
        ROOT / "repro/configs/live_claims.json",
        ROOT / "upstream/arxiv-2605.19052.tar",
        ROOT / "upstream/icml2026-arxiv.tex",
        ROOT / "upstream/icml_appendix.tex",
        RAW,
        verdict_path,
        ROOT / "docs/research_log.md",
    ]
    bundle = ROOT / "outputs/evidence_bundle.jsonl"
    lines = []
    for path in bundle_paths:
        record = {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
        if path.suffix == ".json":
            record["payload"] = json.loads(path.read_text())
        lines.append(json.dumps(record, sort_keys=True, separators=(",", ":")))
    bundle.write_text("\n".join(lines) + "\n")
    print(json.dumps({"all_claims_complete": True, "claims": 6, "possible_points": 12, "metrics": metrics, "bundle_bytes": bundle.stat().st_size, "bundle_sha256": sha256(bundle)}, indent=2))


if __name__ == "__main__":
    main()
