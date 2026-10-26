# E217 Fresh-Session Prompt -- WorldBridge Live Dual-Lane Field Comparability Evaluator Gate

E217 is complete. E216 now produces a validated ordered, non-atomic live trace from real SR and PS bridge authorities. Build a Qt-free deterministic evaluator over that trace. Compare only E213-admitted fields actually observed on both linked snapshots, with explicit per-field exact/tolerance rules and per-pair results. Distinguish comparable pass/mismatch, not observed, and declared loss.

Reject invalid or over-claiming producer payloads. Do not compare SR seconds to PS unit ticks as equal, call the capture atomic, claim replay or lossless parity, auto-correct state, remove mapping-loss labels, change defaults, or elevate GameViewport/Qt into engine authority.

Evidence: full offscreen regression passed 2117 passed, 34 skipped, 55 subtests passed in 217.92s; focused evaluator/GameViewport coverage passed 18 passed and 76 passed, 5 subtests passed; all relevant guards and explicit temporary compilation passed. Continue only with E218, not with replay/default admission.

