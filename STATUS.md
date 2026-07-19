# Status

- OpenReview ID: `OwLuqetJuB`
- arXiv: `2605.19052`
- Effective live contract: 6 anchored claims / 12 possible points
- Owner: `codex-data-driven-lr-six-claims`
- State: `publication_queued`
- Current step: canonical backlog entry 47; shared publisher owns HF publication
- Next: verify the public Space, tags, commit SHA, conclusion, and artifact bucket
- Queue invariant: no backlog entry until every live claim has a substantive outcome and the complete gate passes

## Source audit

The primary arXiv tar is pinned at SHA-256
`c1dea639b1137784cf075b486f29c3b6accbfc34b7a2ba717eb0b02bd347231e`.
The paper is theory-only and supplies an explicit separable binary MILP family.
The Appendix proof of Theorem 6.2 prints two `v_k=0` probabilities with a plus
sign, so they sum to `1+epsilon`. The intended complementary sign is determined
by the stated mean and the adjacent main-text construction. Both the invalid
literal line and the repaired distribution are mandatory controls.

## Completed evidence

- C1 verified: raw ERM decisions independently reconstruct with `N` slope
  `-0.505629`; every cell is below the `O(s^1.5/sqrt(N))` proof envelope.
- C2 verified: 32,766 pairwise packing checks, exact Bernoulli KL, and positive
  Fano factors certify the `Omega(s/sqrt(N))` hard family.
- C3 verified: averaged SGA has `N` slope `-0.497803`, exact linear `s`
  dependence, and maximum theorem-bound ratio `0.114227`.
- C4 verified with the explicit Appendix sign correction: warm-start empirical
  means have `N` slope `-1.007167`, match exact risk within `2.095%`, and the
  corrected Fano family certifies `Omega(s/N)`.
- C5 verified: every covering cell is exact; two independent quadratures agree
  on normalized Dudley constant `5.662939536639`.
- C6 verified: 3,000 producer plus 2,500 independent finite-MILP trials; all
  geometry inequalities pass, while wrong-gradient, max-affine, and omitted
  `sqrt(s)` controls fail.
- Tests: 13/13. Live claim wording: exact 6/6 match. Substantive outcomes: 6/6.
- Evidence bundle: 3,772,558 bytes, SHA-256
  `d604d98ecba61cd4da2f0df513f895c83f6fb239db309c356850636d1dc6efa0`.
- Trackio: ten required pages, exactly one pinned Conclusion cell, and one
  registered local-path dataset matching the bundle size.
- Publication gate passed at `2026-07-19T21:35:51Z`; hygiene found zero secrets,
  environment files, absolute local paths, or forbidden token signatures.
- GitHub: `MachineLearning-Nerd/icml26-repro-OwLuqetJuB-data-driven-lagrangian-relaxation`,
  first gate-complete push `d6b28cb`, queue-compatible manifest commit `fc65f36`.
- Canonical HF backlog: atomically inserted as entry 47 after the GitHub push.
