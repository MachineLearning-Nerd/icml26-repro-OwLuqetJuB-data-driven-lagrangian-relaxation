# Negative controls


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_eb1a559de637", "created_at": "2026-07-19T21:33:16+00:00", "title": "Controls that must fail"}
-->
- Literal Theorem 6.2 `v_k=0` probabilities: **rejected**, sum `1.2` at `epsilon=0.2`.
- Omit `sqrt(s)` from `2B sqrt(s)`: **rejected**, tight witness ratio `4.0` at `s=16`.
- Use `b` instead of `b-Ax*` as gradient: **rejected** in 1,268/2,500 independent cases.
- Replace the pointwise minimum of affine functions by a maximum: **rejected** as concave in 1,155/2,500 cases.
- Mutated source hashes, claim-count drift, raw-risk mutation, packing-cardinality/separation drift, and bundle payload/hash drift are fail-closed in the publication gate and tests.


---
<!-- trackio-cell
{"type": "code", "id": "cell_831eb103d511", "created_at": "2026-07-19T21:33:40+00:00", "title": "Unit and destructive-control tests", "command": ["uv", "run", "pytest", "-q"], "exit_code": 0, "duration_s": 0.613}
-->
````bash
$ uv run pytest -q
````

exit 0 · 0.6s


````output
.......                                                                  [100%]
7 passed in 0.36s

````
