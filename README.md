# Reproduction: Provably Data-driven Lagrangian Relaxation for MILP

This clean-room reproduction targets all six current challenge claims for
OpenReview `OwLuqetJuB` (arXiv `2605.19052`). It uses the paper's explicit
separable binary MILP family, exact finite enumeration, independent numerical
integration and seeded stochastic checks. A malformed probability line in the
warm-start lower-bound appendix is preserved as a must-fail control; the
complementary-sign repair is disclosed and tested.

Run the full evidence path:

```bash
uv sync
uv run python -m repro.src.run_claims
uv run pytest -q
```

No result in this repository is a reduced-dimensional proxy: separability is
used as an exact algebraic reduction, and the reported full `s`-coordinate
risk is exactly `s` times the independently simulated scalar risk.
