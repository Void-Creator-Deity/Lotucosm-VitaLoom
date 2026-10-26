# E316 Checkpoint Restore Witness

## Scope

E316 adds an opt-in, witness-only checkpoint/restore proof on the bounded E313
synthetic harness. It does not change the default dual-lane runtime or claim a
production live adapter.

## Evidence

- The checkpoint has a versioned schema and canonical SHA-256 digest.
- A fresh instance restores the checkpoint and reproduces the post-checkpoint
  trace and final scalar state.
- Lane tick mismatch and checkpoint tampering are rejected.
- Injected PS apply and bridge commit failures are rejected before target
  replacement, and the target fingerprint remains unchanged.
- Runtime status, CI, and release consistency require the E316 CLI witness.

## Explicit limits

The checkpoint contains synthetic SR/PS state, input cursor, randomness
observation, lifecycle metadata, and observation links. It does not restore
production SR entities, a real Pond, component graph state, or live bridge
object identity. `default_ready`, `live_adapter_admitted`, `lossless`, and
`cross_lane_replay` remain false.

## Next gate

E317 must audit the gap between this witness and real PS/Pond persistence, SR
runtime snapshots, and the live capture seam before designing the smallest
opt-in live checkpoint adapter admission conditions.
