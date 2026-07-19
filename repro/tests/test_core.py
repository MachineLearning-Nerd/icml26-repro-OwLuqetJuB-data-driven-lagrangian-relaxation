import math
import json
from pathlib import Path

import numpy as np

from repro.src.core import (
    bernoulli_kl,
    dual_values,
    dudley_integral,
    expected_excess,
    erm_scalar_excess,
    greedy_hamming_packing,
    hard_dual,
    pairwise_hamming,
)
from repro.src.prepublish_gate import validate_bundle, validate_trackio


def test_hard_dual_matches_binary_enumeration():
    rng = np.random.default_rng(1)
    for s in range(1, 9):
        x = np.array([[*map(int, f"{i:0{s}b}")] for i in range(2**s)])
        for _ in range(20):
            c = rng.uniform(0.2, 2, s)
            pi = rng.uniform(0, 2, s)
            value, _, _ = dual_values(pi, c, np.eye(s), np.full(s, 0.5), x)
            assert math.isclose(value, hard_dual(pi, c), abs_tol=1e-12)


def test_population_optimum_and_excess():
    for p, optimum in [(0.4, 1.0), (0.6, 2.0)]:
        grid = np.linspace(0, 3, 3001)
        risks = np.array([expected_excess(np.array([x]), np.array([p])) for x in grid])
        assert abs(grid[np.argmin(risks)] - optimum) < 1e-12
        assert risks.min() >= -1e-12


def test_bernoulli_kl_paper_envelope():
    for eps in np.linspace(1e-4, 0.49, 1000):
        assert bernoulli_kl(float(eps)) <= 4 * eps**2


def test_varshamov_sized_packing():
    for s in [16, 32, 64]:
        rows = greedy_hamming_packing(s)
        distances = pairwise_hamming(rows)
        assert len(rows) == 2 ** (s // 8)
        assert distances.min() >= s // 8


def test_dudley_integral_below_paper_envelope():
    for s in [1, 4, 16, 64, 256]:
        row = dudley_integral(1.0, 2.0, s)
        assert row["integral"] > 0
        assert row["below_envelope"]
        assert math.isclose(row["radius"], 4 * s)


def test_literal_typo_is_not_a_probability_distribution():
    eps = 0.2
    assert not math.isclose((1 + eps) / 2 + (1 + eps) / 2, 1.0)
    assert math.isclose((1 - eps) / 2 + (1 + eps) / 2, 1.0)


def test_erm_selects_population_breakpoint_with_deterministic_samples():
    estimates, risks = erm_scalar_excess(n=10_000, p_high=1.0, repeats=10, seed=1)
    assert np.all(estimates == 2.0)
    assert np.all(risks == 0.0)


def test_tight_gradient_bound_is_attained_by_a_finite_subproblem():
    s = 16
    # The sole feasible point has b=B and Ax=-B in every coordinate.
    pi = np.ones(s)
    c = np.array([0.0])
    a = -np.ones((s, 1))
    b = np.ones(s)
    feasible_x = np.ones((1, 1))
    _, _, gradient = dual_values(pi, c, a, b, feasible_x)
    assert np.linalg.norm(gradient) == 2 * math.sqrt(s)
    assert np.linalg.norm(gradient) > 2  # omitted sqrt(s) control


def test_bundle_round_trip_and_payload_binding(tmp_path):
    root = Path(__file__).resolve().parents[2]
    info = validate_bundle(root / "outputs/evidence_bundle.jsonl", root)
    assert info["records"] == 7
    records = [json.loads(x) for x in (root / "outputs/evidence_bundle.jsonl").read_text().splitlines()]
    records[0]["payload"]["paper_id"] = "mutated"
    bad = tmp_path / "bad.jsonl"
    bad.write_text("\n".join(json.dumps(x) for x in records) + "\n")
    try:
        validate_bundle(bad, root)
    except RuntimeError as exc:
        assert "payload mismatch" in str(exc)
    else:
        raise AssertionError("tampered bundle payload was accepted")


def test_trackio_registration_and_complete_pages():
    root = Path(__file__).resolve().parents[2]
    info = validate_trackio(root, (root / "outputs/evidence_bundle.jsonl").stat().st_size)
    assert info["required_pages"] == 10
    assert info["pinned_conclusion_cells"] == 1


def test_zero_step_sga_control_violates_large_n_bound():
    # With eta=0 the averaged iterate stays at zero and cannot satisfy the rate.
    p = 0.6
    risk = expected_excess(np.array([0.0]), np.array([p]))
    theorem_bound_at_n = 4 / math.sqrt(16384)
    assert risk > theorem_bound_at_n


def test_pinned_contract_has_six_distinct_claims():
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / "repro/configs/live_claims.json").read_text())
    assert contract["paper_id"] == "OwLuqetJuB"
    assert len(contract["claims"]) == len(set(contract["claims"])) == 6


def test_primary_source_contains_literal_typo_and_theorem_anchors():
    root = Path(__file__).resolve().parents[2]
    appendix = (root / "upstream/icml_appendix.tex").read_text()
    main = (root / "upstream/icml2026-arxiv.tex").read_text()
    assert "If $v_k = 0$: $\\bbP(c_k = 2) = \\frac{1 + \\epsilon}{2}$" in appendix
    for anchor in [
        "thm:upper-bound-learning-lagrangian", "thm:minimax-lower-bound",
        "thm:minimax-SGA", "thm:upper-bound-warm-start",
        "thm:minimax-lower-bound-warm-start", "lm:covering-upper-bound",
        "prop:geometric-property",
    ]:
        assert anchor in main
    estimates, risks = erm_scalar_excess(n=10_000, p_high=0.0, repeats=10, seed=1)
    assert np.all(estimates == 1.0)
    assert np.all(risks == 0.0)
