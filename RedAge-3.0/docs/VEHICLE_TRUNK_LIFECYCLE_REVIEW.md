# Vehicle trunk inventory — close lifecycle review

## VEH-012 — OtherClose does not release the vehicle trunk reservation

**Приоритет: средний по доступности; статически подтверждён. Runtime reproduction не выполнялся.**

### Evidence and flow

- `Core/Selecting.cs` vehicleSelected branch 3 sets `vehicleLocalData.BagInUse = true`, stores the vehicle in `sessionData.SelectData.SelectedVeh`, then opens its inventory through `LoadOtherItemsData`.
- The CEF inventory's `closeOther()` handler clears only the client-side other-pane data and calls `client.inventory.OtherClose` (`src_cef/.../inventory.svelte:450-457`).
- The client bridge forwards that event to `server.gamemenu.inventory.otherclose` (`src_client/inventory/index.js`, `client.inventory.OtherClose` handler); `Chars.Events.InventoryOtherClose` calls `Repository.OtherClose`.
- `Chars.Repository.OtherClose` removes the player from `InventoryOtherPlayers` and sets `InventoryOtherLocationName = null`, but does not clear `SelectData.SelectedVeh` or reset the selected vehicle's `BagInUse`.
- The reset currently exists in the full `ItemsClose` path, before it calls `OtherClose`; disconnect cleanup also releases `BagInUse`. Therefore closing only the other pane (or replacing its context through another `LoadOtherItemsData`) can leave the old vehicle marked occupied until the full inventory is closed or the player disconnects.
- The next player attempting to open that trunk is rejected by the `BagInUse` guard in `Core/Selecting.cs`. The issue is a stale reservation/availability failure, not evidence of unauthorized item access.

**Impact boundary:** this is a per-vehicle availability lock. Static code proves the cleanup gap and the later guard; actual user-visible duration and event ordering should be verified on RAGE staging. Do not describe it as a remote exploit or permanent lock: full inventory close and disconnect currently have release paths.

### Remediation (not implemented)

Make the vehicle reservation lifecycle single-owner and idempotent. A shared release helper should:
1. Resolve the exact `SelectedVeh` safely and clear its `BagInUse` only if the reservation belongs to this player/session (prefer storing an explicit holder/session token rather than a bare Boolean).
2. Clear `SelectedVeh` on every vehicle-container close/replacement path.
3. Be called by `OtherClose`, full `ItemsClose`, disconnect, vehicle deletion/replacement and any explicit session revocation.
4. Avoid releasing another player's newer reservation if stale state or entity reuse occurs.

Do not simply clear a Boolean without checking reservation ownership if the implementation is upgraded to support concurrent access.

### Regression matrix

- Open vehicle trunk, close only the other pane while keeping the main inventory open; assert `BagInUse == false`, `SelectedVeh == null`, and a second player can open the trunk.
- Open vehicle trunk, switch directly to another `LoadOtherItemsData` container; verify the old vehicle reservation is released before the new container is installed.
- Full inventory close and disconnect continue to release reservations exactly once.
- Repeated `otherclose`, repeated full close, and close-after-vehicle-delete are safe and do not throw.
- Two players race to open the same trunk; only the reservation owner can release it, and a stale close from the former owner cannot clear a newer owner's reservation.
- Test own/key-shared/faction/organization trunks and legitimate access policy from `INV-012`.

**Scope boundary:** VEH-012 is separate from INV-012. INV-012 concerns authorization revalidation during item operations; VEH-012 concerns releasing the vehicle's occupancy reservation when the auxiliary inventory pane closes.
