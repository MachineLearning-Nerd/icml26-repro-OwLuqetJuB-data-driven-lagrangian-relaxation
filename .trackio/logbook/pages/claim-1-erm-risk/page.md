# Claim 1 - ERM risk


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_46bdb7c8d1cd", "created_at": "2026-07-19T21:33:13+00:00", "title": "Verified - Theorem 5.5"}
-->
**Claim:** expected ERM excess risk is `O(s^1.5/sqrt(N))`.

Independent reconstruction of every raw ERM decision on the paper's hard family gives an `N` log-slope of **-0.505629** and exact linear dependence on `s`. Every cell remains below the paper's Dudley/Rademacher upper envelope. This directly instantiates the estimator in addition to checking the proof constants.
