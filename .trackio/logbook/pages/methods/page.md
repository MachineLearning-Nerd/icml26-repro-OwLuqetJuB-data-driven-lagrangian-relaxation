# Methods


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_929ae03fadb7", "created_at": "2026-07-19T21:33:16+00:00", "title": "Exact scope and independence"}
-->
## Primary implementation

- Exact finite feasible-set enumeration for general Lagrangian subproblems.
- Exact coordinatewise dual formula on the paper's binary hard MILP.
- Deterministic Varshamov-sized Hamming packings and exact Bernoulli KL.
- Raw ERM, averaged-SGA, and warm-start trials across `s={16,32,64}` and `N={256,1024,4096,16384}`.
- Gauss-Laguerre entropy integration.

## Independent verification

The verifier does not trust summary fields. It rebuilds raw ERM/SGA risks, pairwise Hamming distances, KL and Fano constants, warm-start aggregates, covering cells, and source hashes. It uses a separate dense entropy integration and 2,500 fresh finite-MILP trials with a separate seed and implementation.

Separability is an exact algebraic reduction: a full `s`-coordinate utility is a sum of scalar utilities, so its expected risk is exactly `s` times the scalar risk, not a reduced-scale proxy.


---
<!-- trackio-cell
{"type": "code", "id": "cell_71f4078ff25a", "created_at": "2026-07-19T21:33:39+00:00", "title": "Independent raw-evidence verifier", "command": ["uv", "run", "python", "-m", "repro.src.verify_all"], "exit_code": 0, "duration_s": 0.617}
-->
````bash
$ uv run python -m repro.src.verify_all
````

exit 0 · 0.6s


````output
{
  "all_claims_complete": true,
  "claims": 6,
  "possible_points": 12,
  "metrics": {
    "source_pins": true,
    "erm_n_slope": -0.5056292231329746,
    "packing_pairs": 32766,
    "min_fano_error": 0.2737854175886105,
    "sga_n_slope": -0.4978030069946627,
    "max_sga_bound_ratio": 0.11422749804332853,
    "warm_n_slope": -1.0071673350203592,
    "max_warm_exact_relative_error": 0.020945720995465638,
    "rademacher_normalized_constant": 5.662939536639223,
    "producer_geometry_trials": 3000,
    "independent_geometry": {
      "trials": 2500,
      "min_concavity_margin": -1.7763568394002505e-15,
      "min_supergradient_margin": -1.7763568394002505e-15,
      "max_norm_ratio": 0.7034745386687321,
      "wrong_gradient_failures": 1268,
      "max_control_failures": 1155
    }
  },
  "bundle_bytes": 3772558,
  "bundle_sha256": "d604d98ecba61cd4da2f0df513f895c83f6fb239db309c356850636d1dc6efa0"
}

````


---
<!-- trackio-cell
{"type": "artifact", "id": "cell_ddd049311728", "created_at": "2026-07-19T21:33:39+00:00", "title": "Artifact: evidence_bundle.jsonl", "path": "outputs/evidence_bundle.jsonl", "size": 3772558, "artifact_type": "dataset", "auto": true}
-->
**📦 Artifact** `outputs/evidence_bundle.jsonl` · dataset · 3.8 MB

trackio-local-path://outputs/evidence_bundle.jsonl


---
<!-- trackio-cell
{"type": "code", "id": "cell_c4cb70208222", "created_at": "2026-07-19T21:35:47+00:00", "title": "Complete live-contract publication gate", "command": ["uv", "run", "python", "-m", "repro.src.prepublish_gate"], "exit_code": 0, "duration_s": 3.967}
-->
````bash
$ uv run python -m repro.src.prepublish_gate
````

exit 0 · 4.0s


````output
{
  "all_claims_complete": true,
  "claims": 6,
  "possible_points": 12,
  "metrics": {
    "source_pins": true,
    "erm_n_slope": -0.5056292231329746,
    "packing_pairs": 32766,
    "min_fano_error": 0.2737854175886105,
    "sga_n_slope": -0.4978030069946627,
    "max_sga_bound_ratio": 0.11422749804332853,
    "warm_n_slope": -1.0071673350203592,
    "max_warm_exact_relative_error": 0.020945720995465638,
    "rademacher_normalized_constant": 5.662939536639223,
    "producer_geometry_trials": 3000,
    "independent_geometry": {
      "trials": 2500,
      "min_concavity_margin": -1.7763568394002505e-15,
      "min_supergradient_margin": -1.7763568394002505e-15,
      "max_norm_ratio": 0.7034745386687321,
      "wrong_gradient_failures": 1268,
      "max_control_failures": 1155
    }
  },
  "bundle_bytes": 3772558,
  "bundle_sha256": "d604d98ecba61cd4da2f0df513f895c83f6fb239db309c356850636d1dc6efa0"
}
.............                                                            [100%]
13 passed in 0.82s
{
  "bundle": {
    "bytes": 3772558,
    "records": 7,
    "sha256": "d604d98ecba61cd4da2f0df513f895c83f6fb239db309c356850636d1dc6efa0"
  },
  "claims": {
    "exact_wording_match": true,
    "falsified": 0,
    "live_claim_count": 6,
    "possible_points": 12,
    "substantive": 6,
    "verified": 6
  },
  "hygiene": {
    "env_files": 0,
    "forbidden_hits": 0,
    "publishable_text_files_scanned": 29
  },
  "paper_id": "OwLuqetJuB",
  "passed": true,
  "passed_at": "2026-07-19T21:35:47.776000+00:00",
  "tests": "all passed",
  "trackio": {
    "pinned_conclusion_cells": 1,
    "registered_bundle_bytes": 3772558,
    "required_pages": 10
  }
}

````
