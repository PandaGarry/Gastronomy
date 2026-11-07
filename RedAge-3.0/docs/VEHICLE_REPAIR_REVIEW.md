# Self-repair dialog callback — статический review

Обновлено: 2026-11-07. Проверена цепочка `dialogCallback` → `RepairMyVeh` → vehicle repair/payment. Это один путь; review всего vehicle/garage subsystem не начат. C# build, direct remote and RAGE staging не запускались.

## VEH-001 — arbitrary dialog callback can invoke self-repair outside the configured interaction point

**Приоритет: низкий/средний; policy-dependent.**

- `Main.cs:2372-2373` exposes `[RemoteEvent("dialogCallback")]` with client-supplied `callback` string and `yes` boolean. In its shown setup, the handler validates player/session/account/character but does not check that this callback was opened by a server-owned pending dialog or consume a repair intent.
- `Main.cs:2416-2442` dispatches the string `RepairMyVeh`. It requires the player to be in a vehicle and cached money >= `$500`, then calls `VehicleManager.RepairCar(vehicle)`, calls `Wallet.Change(player,-500)` without checking its bool result, logs success and notifies. The repair occurs before the debit result is known. The “mechanic currently available” loop is commented out at `Main.cs:2423-2434`.
- The apparent legitimate interaction that opens the dialog, `Core/VehicleSync.cs:494-508`, is entirely inside a block comment. It would create a colshape at a repair location and call `openDialog("RepairMyVeh", ...)`; the in-text localization says this is a local self-repair for `$500` if no mechanic is on duty. No other active `RepairMyVeh` call site was found in the checked source tree.
- `Core/Vehicle.cs:666-678` `RepairCar` merely calls `vehicle.Repair()` when vehicle-local data exists; it enforces no repair-location or mechanic-availability condition.

Thus a modified client can invoke the active generic `dialogCallback` directly with `callback="RepairMyVeh"` and `yes=true`; the server branch can repair the current vehicle without proving an open, nearby service interaction. It still checks for `$500` beforehand, so this is not a claim of free repair under normal wallet operation. If `Wallet.Change` fails after repair (for example, because server stop state makes negative changes fail), the unchecked result leaves the repair applied; confirm and test that secondary path. Since the intended physical point is commented out and policy/feature status is unknown, establish owner intent before treating the location bypass as a confirmed gameplay exploit.

The branch also calls `UpdateReward(player, 13)`, but `13` is not a task ID in the current Season4 catalog; through `UpdateReward`'s `FirstOrDefault` null return this progress call is a no-op in this season. This review does not claim BattlePass progress can be earned from this repair path.

**Remediation (не внедрено):** if self-repair is intended, open a server-owned short-lived repair intent only from an active repair interaction; at confirmation revalidate the vehicle, player location/dimension, and mechanic-availability policy. Debit successfully before repair or use an atomic/compensating receipt. If self-repair was retired, remove/disable the stale callback case. Never treat a client-provided generic callback name as proof of an offered dialog.

**Regression:** direct callback from road/house/interior, from valid repair point, with/without on-duty mechanic, no pending intent, wrong vehicle/stale vehicle, insufficient funds and `Wallet.Change` failure; assert repair, balance, notification and GameLog consistency. If feature disabled, all direct callbacks must no-op. Confirm the commented callsite's intended deployment status.

## Границы

Только source evidence; owner gameplay policy, actual deployment, event marshalling, C# build, wallet failure and RAGE runtime remain unverified. Общий vehicle/garage/property audit остаётся открытым.
