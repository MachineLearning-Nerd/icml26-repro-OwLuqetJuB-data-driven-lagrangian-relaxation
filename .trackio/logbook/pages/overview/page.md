# Overview


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_9336dacda030", "created_at": "2026-07-19T21:33:12+00:00", "title": "Six-claim current contract"}
-->
## Outcome

All **six current anchored claims** have substantive, independently recomputed outcomes: **6 verified / 0 falsified / 0 toy**, for **12 possible points**. The verification uses the paper's exact separable MILP hard family and general finite feasible-set enumeration.

The primary source is arXiv `2605.19052`, pinned by tar SHA-256 `c1dea639b1137784cf075b486f29c3b6accbfc34b7a2ba717eb0b02bd347231e`.

## Important source correction

The Appendix proof of Theorem 6.2 prints both `v_k=0` probabilities with `(1+epsilon)/2`; they sum to `1+epsilon` and therefore are not a distribution. The complementary-sign repair is uniquely consistent with the stated mean and adjacent construction. The literal line is preserved as a must-fail control.


---
<!-- trackio-cell
{"type": "code", "id": "cell_4b833a4567a9", "created_at": "2026-07-19T21:33:38+00:00", "title": "Execute all six claim paths", "command": ["uv", "run", "python", "-m", "repro.src.run_claims"], "exit_code": 0, "duration_s": 3.386}
-->
````bash
$ uv run python -m repro.src.run_claims
````

exit 0 · 3.4s


````output
{
  "paper_id": "OwLuqetJuB",
  "source_pins": true,
  "typo_present": true,
  "packing_pairs": 32766,
  "sga_slope_n": -0.4978030069946627,
  "warm_slope_n": -1.0071673350203592,
  "geometry_trials": 3000
}

````
