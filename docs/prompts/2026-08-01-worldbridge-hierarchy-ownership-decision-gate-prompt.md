# E209 Fresh-Session Prompt -- WorldBridge Hierarchy Ownership Decision Gate

E209 is complete with an explicit rejection. `EntityBase` parent/children is live graph behavior: it affects world coordinates and recursive update. Pond root registration is separate and unreconciled; a child can remain a root, which makes a pond tick dispatch it through both membership paths. `PondSerializer` emits independent organism records without parent/children fields, and WorldBridge has no hierarchy route. Focused coverage passed `13 passed in 1.05s`; the prior fresh runtime baseline remains `2062 passed, 34 skipped, 50 subtests passed in 225.92s`.

The one next gate is E210: audit memory-gene ownership and persistence. Do not copy a memory-gene field merely because both lanes mention genes; prove its inheritance, serializer, runtime-memory, command/scene authority, and replay implications first.
