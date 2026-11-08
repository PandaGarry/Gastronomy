# AirDrop remote authorization and lock state review

## INV-013 — AirDrop lock/hack and loot remotes are not bound to the player's crate context

**Приоритет: высокий; missing server-side spatial/session validation statically confirmed. Runtime exploitation not reproduced.**

### Evidence

- `Events/AirDrop/Repository.cs:424-444`: `IsPlayerToEvents` checks whether the player's fraction/organization name exists in `TeamsInfo`; it does not check `Dimension == 100`, `IsInAirDropZone` or distance to a crate.
- `PayAirdropOrder` registers the ordering team in `TeamsInfo` before starting the event (around :942-960), so team registration is not proof that this specific player is physically at the crate or in the event dimension.
- `StartedHack` remote (:638-707) checks team membership, feature flag, admin status and possession of an ArmyLockpick, then sets `AirdropHackPlayerInfo` and the generic `sessionData.IsAirDropHacking`. It does not check the player's position/dimension against the selected `AirDropData.Position`, nor bind a server-side active crate ID to the player.
- `AirdropChangeLockStatus` remote (:547-593) trusts client-supplied `health` and assigns it directly to the crate (:562). It checks only team membership and the generic `IsAirDropHacking` Boolean; it does not prove that this player started hacking this exact crate, validate progress/time/health range, or verify proximity. A client can submit zero/negative health immediately; the server then performs its 50% unlock roll and consumes an ArmyLockpick if the resulting health is <= 0.
- `OpenInventory` remote (:597-636) checks only `IsPlayerToEvents`. When the crate lock is open it calls `LoadOtherItemsData("airdrop", ShapeId, ...)` (:627), without requiring the caller to be near the crate or in dimension 100.
- Client `src_client/events/airdrop.js:156-185` performs the countdown locally and sends the resulting health to the server. This is not an authoritative server-side lock timer.

### Impact boundary

A member of a team registered in `TeamsInfo` who has an ArmyLockpick can attempt the hack remotes without the server proving physical presence at the target crate. If the server accepts the client-supplied completion value and the random unlock succeeds, the same team-member gate permits opening the loot container remotely. The static path is clear; successful RAGE execution, item extraction and economy impact still require staging reproduction. Do not claim a live theft or production exploitation.

### Remediation (not implemented)

- Replace the generic Boolean with a server-owned, expiring hack intent bound to player, exact `DropId`, event generation, dimension, start position and start timestamp.
- Require the player to be in the active event dimension and within a small server-measured radius of the exact crate at start, progress and open.
- Derive progress server-side from elapsed time; do not accept client health as authoritative. Validate all transitions and consume one lockpick exactly once after a valid completed attempt.
- On every progress/finish callback require `AirdropHackPlayerInfo == player` and exact intent `DropId`; revoke on movement, dimension change, event end, disconnect, timeout or crate replacement.
- Require the open remote to revalidate event state, exact crate existence/unlocked state, dimension and proximity before calling `LoadOtherItemsData`.

### Regression matrix

- Registered team member outside dimension 100 / outside event zone calls start-hack, change-lock and open remotes; all must reject without changing lock, inventory, item cache or event state.
- At the crate, test valid local hack and open; wrong DropId, another crate ID, replay, duplicate progress and stale intent must reject.
- Submit health values `-1`, `0`, `1`, `20`, `100`, `int.MaxValue`; server progress must be time/state-derived and bounded.
- Start hacking crate A, then submit completion for crate B; reject. Start a MatWar hack then attempt AirDrop completion (and vice versa); event-specific intents must not cross-authorize.
- Move away/change dimension/leave team/disconnect/event-end during hack; intent and hacker pointer must be cleared.
- Verify exactly-once lockpick consumption, random outcome and loot access under normal play.

**Scope boundary:** INV-013 is the AirDrop-specific event lock and loot authorization defect. Generic container mutation policy remains tracked by INV-003; vehicle session authorization remains INV-012.
