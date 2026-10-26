# E205 Fresh-Session Prompt -- WorldBridge Kinematic Mapping-Loss Contract Gate

E205 is complete. The bridge now maps finite two-component `velocity` and `acceleration` values at creation and in both existing sync directions using detached copies and malformed/non-finite no-ops. The audit marks `velocity_acceleration` covered and no longer lists it as a known loss, but it remains explicitly `lossless=false` and `default_ready=false`. Fresh complete proof is `2062 passed, 34 skipped, 50 subtests passed in 225.92s`.

The one next gate is E206: make an authority decision for `active_visible_state`. Do not copy those flags just because both classes inherit them: establish whether PS behavior honors `active`, and whether `visible` has a real PS rendering consumer. Preserve all pilot/non-lossless/no-tick-merge constraints.
