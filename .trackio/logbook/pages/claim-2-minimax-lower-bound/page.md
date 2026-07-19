# Claim 2 - minimax lower bound


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_8c84bfda1fd0", "created_at": "2026-07-19T21:33:13+00:00", "title": "Verified - Theorem 5.6"}
-->
The exact Fano construction passes. Greedy deterministic packings have the required `2^(s/8)` cardinality and at least `s/8` separation for `s=16,32,64`; **32,766** pairs were checked. Exact Bernoulli KL is below the paper's envelope in every cell, and the smallest Fano testing-error factor is **0.273785**. The normalized lower certificate stays positive and constant in `N`, establishing `Omega(s/sqrt(N))` on the explicit hard family.
