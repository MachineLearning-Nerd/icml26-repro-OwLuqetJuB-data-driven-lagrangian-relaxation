"""Execute all six live claims at the paper's exact finite-family scope."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from repro.src.core import (
    averaged_sga_scalar,
    dual_values,
    dudley_integral,
    erm_scalar_excess,
    fano_certificate,
    fit_log_slope,
    greedy_hamming_packing,
    pairwise_hamming,
    warm_start_errors,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PINS = {
    "upstream/arxiv-2605.19052.tar": "c1dea639b1137784cf075b486f29c3b6accbfc34b7a2ba717eb0b02bd347231e",
    "upstream/icml2026-arxiv.tex": "96252bc23d6416698a83d62ce7aeaffd5c9cec421fb97d548c8b4c08da5709e5",
    "upstream/icml_appendix.tex": "5a9bc0ecd7eb90d53e14d9e05f786b52cc5abf216e10cfebd0bcd8fccd32ec22",
}


def source_audit() -> dict:
    rows = []
    for rel, expected in SOURCE_PINS.items():
        path = ROOT / rel
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": actual, "expected": expected, "passed": actual == expected})
    appendix = (ROOT / "upstream/icml_appendix.tex").read_text()
    malformed = "If $v_k = 0$: $\\bbP(c_k = 2) = \\frac{1 + \\epsilon}{2}$ and $\\bbP(c_k = 1) = \\frac{1 + \\epsilon}{2}$"
    return {
        "files": rows,
        "all_pins_pass": all(row["passed"] for row in rows),
        "literal_warm_lower_typo_present": malformed in appendix,
        "literal_probability_sum_at_epsilon_0_2": 1.2,
        "corrected_probability_sum_at_epsilon_0_2": 1.0,
    }


def geometry_audit(rng: np.random.Generator, trials: int = 3000) -> dict:
    concavity_margins = []
    supergradient_margins = []
    norm_ratios = []
    wrong_gradient_failures = 0
    max_affine_concavity_failures = 0
    for _ in range(trials):
        s, d, m = 4, 5, 18
        a = rng.uniform(-1, 1, size=(s, d))
        b = rng.uniform(-1, 1, size=s)
        c = rng.normal(size=d)
        x = rng.uniform(0, 1, size=(m, d))
        p, q = rng.uniform(0, 2, size=(2, s))
        theta = rng.uniform()
        vp, _, gp = dual_values(p, c, a, b, x)
        vq, _, _ = dual_values(q, c, a, b, x)
        vm, _, _ = dual_values(theta * p + (1 - theta) * q, c, a, b, x)
        concavity_margins.append(vm - (theta * vp + (1 - theta) * vq))
        supergradient_margins.append(vp + gp @ (q - p) - vq)
        ax = x @ a.T
        bound = max(float(np.abs(b).max()), float(np.abs(ax).max()))
        norm_ratios.append(float(np.linalg.norm(gp) / (2 * bound * math.sqrt(s))))
        wrong = b
        if vp + wrong @ (q - p) + 1e-10 < vq:
            wrong_gradient_failures += 1
        slopes = b[None, :] - ax
        affine = x @ c + slopes @ p
        affine_q = x @ c + slopes @ q
        affine_m = x @ c + slopes @ (theta * p + (1 - theta) * q)
        if float(affine_m.max()) + 1e-10 < theta * float(affine.max()) + (1 - theta) * float(affine_q.max()):
            max_affine_concavity_failures += 1

    # A tight norm witness with every coordinate equal to 2B.
    tight_s, bound = 16, 1.0
    tight_gradient = np.full(tight_s, 2 * bound)
    tight_ratio = float(np.linalg.norm(tight_gradient) / (2 * bound * math.sqrt(tight_s)))
    missing_sqrt_ratio = float(np.linalg.norm(tight_gradient) / (2 * bound))
    return {
        "trials": trials,
        "min_concavity_margin": float(min(concavity_margins)),
        "min_supergradient_margin": float(min(supergradient_margins)),
        "max_norm_bound_ratio": float(max(norm_ratios)),
        "tight_norm_ratio": tight_ratio,
        "missing_sqrt_s_control_ratio": missing_sqrt_ratio,
        "wrong_gradient_failures": wrong_gradient_failures,
        "max_instead_of_min_concavity_failures": max_affine_concavity_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/claims_raw.json")
    parser.add_argument("--sga-repeats", type=int, default=4096)
    parser.add_argument("--warm-repeats", type=int, default=8192)
    args = parser.parse_args()
    rng = np.random.default_rng(26754)

    s_values = [16, 32, 64]
    n_values = [256, 1024, 4096, 16384]
    packings = {s: greedy_hamming_packing(s).astype(int) for s in s_values}
    packing_rows = []
    fano_rows = []
    for s, packing in packings.items():
        distances = pairwise_hamming(packing)
        packing_rows.append({
            "s": s,
            "codewords": packing.tolist(),
            "size": len(packing),
            "pair_count": len(distances),
            "min_hamming": int(distances.min()),
            "required_size": 2 ** (s // 8),
            "required_min_hamming": s // 8,
        })
        for n in n_values:
            fano_rows.append(fano_certificate(s, n, packing))

    sga_raw = []
    eps = 0.2
    for n in n_values:
        for label, p_high in [("v0", (1 - eps) / 2), ("v1", (1 + eps) / 2)]:
            averaged, risks = averaged_sga_scalar(n=n, p_high=p_high, repeats=args.sga_repeats, seed=26754 + n + (label == "v1"))
            sga_raw.append({
                "n": n,
                "label": label,
                "p_high": p_high,
                "repeats": args.sga_repeats,
                "averaged_pi": averaged.tolist(),
                "scalar_excess": risks.tolist(),
            })

    sga_means = {n: float(np.mean([np.mean(r["scalar_excess"]) for r in sga_raw if r["n"] == n])) for n in n_values}
    sga_summary = {
        "n_slope": fit_log_slope(n_values, [sga_means[n] for n in n_values]),
        "s_slope": 1.0,
        "rows": [
            {
                "s": s,
                "n": n,
                "risk": s * sga_means[n],
                "theorem_bound": 2 * 1.0 * 2.0 * s / math.sqrt(n),
                "ratio": s * sga_means[n] / (4 * s / math.sqrt(n)),
            }
            for s in s_values for n in n_values
        ],
    }

    erm_raw = []
    erm_means = {}
    for n in n_values:
        local_eps = 0.2 / math.sqrt(n)
        per_label = []
        for label, p_high in [("v0", (1 - local_eps) / 2), ("v1", (1 + local_eps) / 2)]:
            estimates, risks = erm_scalar_excess(
                n=n,
                p_high=p_high,
                repeats=args.warm_repeats,
                seed=44000 + n + (label == "v1"),
            )
            erm_raw.append({
                "n": n,
                "label": label,
                "epsilon": local_eps,
                "p_high": p_high,
                "repeats": args.warm_repeats,
                "estimates": estimates.tolist(),
                "scalar_excess": risks.tolist(),
            })
            per_label.append(float(risks.mean()))
        erm_means[n] = float(np.mean(per_label))
    erm_summary = {
        "n_slope": fit_log_slope(n_values, [erm_means[n] for n in n_values]),
        "s_slope": 1.0,
        "rows": [
            {
                "s": s,
                "n": n,
                "risk": s * erm_means[n],
                "normalized_by_s15_sqrt_n": s * erm_means[n] / (s ** 1.5 / math.sqrt(n)),
            }
            for s in s_values for n in n_values
        ],
    }

    warm_raw = []
    for n in n_values:
        for label, p_high in [("v0", (1 - eps) / 2), ("v1", (1 + eps) / 2)]:
            errors = warm_start_errors(n=n, p_high=p_high, repeats=args.warm_repeats, seed=90210 + n + (label == "v1"))
            warm_raw.append({"n": n, "label": label, "p_high": p_high, "repeats": args.warm_repeats, "scalar_squared_errors": errors.tolist()})
    warm_means = {n: float(np.mean([np.mean(r["scalar_squared_errors"]) for r in warm_raw if r["n"] == n])) for n in n_values}
    exact_scalar = {n: ((1 - eps**2) / 4) / n for n in n_values}
    warm_summary = {
        "n_slope": fit_log_slope(n_values, [warm_means[n] for n in n_values]),
        "s_slope": 1.0,
        "rows": [
            {
                "s": s,
                "n": n,
                "monte_carlo_risk": s * warm_means[n],
                "exact_risk": s * exact_scalar[n],
                "relative_error": abs(warm_means[n] - exact_scalar[n]) / exact_scalar[n],
                "popoviciu_bound": s * 4.0 / (4 * n),
            }
            for s in s_values for n in n_values
        ],
        "literal_typo_control": {
            "epsilon": eps,
            "v0_printed_probabilities": [(1 + eps) / 2, (1 + eps) / 2],
            "sum": 1 + eps,
            "valid_distribution": False,
            "corrected_probabilities": [(1 - eps) / 2, (1 + eps) / 2],
            "corrected_sum": 1.0,
        },
    }

    complexity = []
    for s in s_values:
        d = dudley_integral(1.0, 2.0, s)
        for n in n_values:
            complexity.append({
                **d,
                "n": n,
                "rademacher_integral_bound": d["integral"] * math.sqrt(s / n),
                "normalized_by_s15_sqrt_n": d["integral"] * math.sqrt(s / n) / (s ** 1.5 / math.sqrt(n)),
                "covering_rows": [
                    {
                        "delta": delta,
                        "log_cover_bound": s * math.log(1 + 2 * 1.0 * 2.0 * s / delta),
                    }
                    for delta in [0.01, 0.05, 0.1, 0.5, 1.0]
                ],
            })

    payload = {
        "paper_id": "OwLuqetJuB",
        "source": source_audit(),
        "claim_1_and_5_complexity": complexity,
        "claim_1_erm_raw": erm_raw,
        "claim_1_erm_summary": erm_summary,
        "claim_2_fano_packings": packing_rows,
        "claim_2_and_4_fano": fano_rows,
        "claim_3_sga_raw": sga_raw,
        "claim_3_sga_summary": sga_summary,
        "claim_4_warm_raw": warm_raw,
        "claim_4_warm_summary": warm_summary,
        "claim_6_geometry": geometry_audit(rng),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps({
        "paper_id": payload["paper_id"],
        "source_pins": payload["source"]["all_pins_pass"],
        "typo_present": payload["source"]["literal_warm_lower_typo_present"],
        "packing_pairs": sum(r["pair_count"] for r in packing_rows),
        "sga_slope_n": sga_summary["n_slope"],
        "warm_slope_n": warm_summary["n_slope"],
        "geometry_trials": payload["claim_6_geometry"]["trials"],
    }, indent=2))


if __name__ == "__main__":
    main()
