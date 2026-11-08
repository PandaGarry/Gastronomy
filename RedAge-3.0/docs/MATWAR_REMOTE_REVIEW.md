# MatWar remote authorization and loot lifecycle review

## INV-014 — MatWar crate hack/open remotes lack active-event and spatial authorization

**Приоритет: высокий; missing checks statically confirmed. Runtime exploitation not reproduced.**

### Evidence

- `Fractions/Manager.cs:3171-3204` starts MatWar, resets `MatWarDropHealth` to 100, chooses the drop position and populates `matwar_100`.
- `StartedMatWarHack` remote (:3335-3397) checks character/session, feature flag, admin level and ArmyLockpick, then for ShapeId 100 sets `MatWarDropHackPlayerInfo` and `sessionData.IsAirDropHacking`. It does not check `isWar`, faction/event eligibility, player dimension or distance to `MatWarDropsPositions[MatWarDropPositionIndex]`.
- `MatWarDropChangeLockStatus` remote (:3401-3448) requires only the generic `IsAirDropHacking` Boolean and ShapeId 100; it assigns client-supplied `health` directly to `MatWarDropHealth` (:3418) and performs the 50% unlock roll when health <= 0. It does not prove that this player owns the active MatWar hack intent or validate elapsed time, progress or health bounds.
- `OpenMatWarInventory` remote (:3453-3486) checks only character data and ShapeId 100. When health <= 0 it calls `LoadOtherItemsData("matwar", ...)` (:3480) without checking `isWar`, current drop existence, player position or dimension.
- The same `SessionData.IsAirDropHacking` Boolean is used by AirDrop and MatWar handlers; it is not an event-specific/player-object binding.
- `endWar` (:3236 onward) stops the timer and deletes client-side crate objects, but does not reset `MatWarDropHealth` or remove `matwar_100` inventory. The next `startWar` removes/repopulates that location (:3194-3204). The hack/open remotes do not require `isWar == true`, so stale event inventory remains server-side between wars and the handlers can still address it.

### Impact boundary

A character with an ArmyLockpick can attempt the MatWar start-hack remote without the server proving proximity or that a war is active, then submit a client-selected completion value. If the random unlock succeeds, the open remote can expose the shared MatWar loot location. Because endWar removes only the client object and leaves the server inventory/health state intact until the next startWar, stale loot may remain addressable between events. This is a static exploit path, not a runtime-confirmed theft.

### Remediation (not implemented)

- Require `isWar` and the correct current MatWar event generation for status, start, progress and open endpoints.
- Verify the player is in the expected dimension and within a small server-measured radius of the current `MatWarDropsPositions[MatWarDropPositionIndex]` on every endpoint.
- Use a dedicated MatWar hack intent bound to player, ShapeId, event generation and timestamp; do not reuse `IsAirDropHacking` as cross-event authorization.
- Derive lock progress server-side; validate monotonic state and consume the ArmyLockpick exactly once only after valid completion.
- Require `MatWarDropHackPlayerInfo == player` for completion; clear intent/hacker on movement, timeout, disconnect and event end.
- On `endWar`, close/revoke all active MatWar container sessions, remove `matwar_100` inventory, reset lock/hacker state and invalidate the event generation before deleting client objects.

### Regression matrix

- With no active war, direct-call check/start/progress/open endpoints; all must reject and no MatWar inventory must be exposed.
- During an active war, call from a distant position, wrong dimension, nonparticipant faction and stale client crate ID; reject.
- At the valid drop, test normal unlock/open, wrong ShapeId, arbitrary health values, instant zero, negative values, replay and duplicate completion.
- Start an AirDrop hack and call MatWar completion; start MatWar hack and call AirDrop completion; cross-event calls must reject.
- End the war while locked, unlocked and while a player has an active hack/container; all sessions and items must be invalidated, and direct remote calls between wars must reject.
- Verify ArmyLockpick consumption exactly once, no item duplication/loss, and next startWar creates only a fresh inventory generation.

**Scope boundary:** INV-014 is the MatWar event lifecycle/access defect. INV-003 remains the shared container mutation policy issue; INV-013 tracks the separate AirDrop remote path.
