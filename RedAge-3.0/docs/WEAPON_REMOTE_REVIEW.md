# Weapon and ammunition remotes — static review

Обновлено: 2026-11-07. Traced weapon remove/reload/ammo-return/equip remotes through the client weapon bridge and inventory helpers. Static-only: no RAGE execution, CEF/client native verification, DB staging or live inventory test. Findings remain remediation work; this review does not imply a fix or completion.

## INV-010 — direct ammo-return remote can mint ammunition

**Приоритет: высокий; unchecked client count and inventory mutation path confirmed statically; successful live duplication and exact client event marshalling require RAGE staging.**

- `server.weapon.ammoin` takes client-controlled `hash` and `ammoInClip` and calls `WeaponRepository.RemoveAmmo` (`Core/WeaponRepository.cs:564-593`). The handler maps any recognized weapon hash to its ammunition item, but does not verify that this is the player's active/server-tracked weapon or that the amount corresponds to rounds actually removed from it.
- It calls `Chars.Repository.isFreeSlots(player, aType, ammoInClip, false)` before capping the supplied amount to `WeaponsClipsMax[ItemId]`. `isFreeSlots` returns a positive overflow/excess count when requested count exceeds ammo capacity (`Chars/Repository.cs:4352-4455`), but `RemoveAmmo` treats that return as the amount to add. With no existing ammo and a request of 1,000 pistol rounds, static arithmetic gives 700 (`pistol ammo effective max 300`, stack 100 × `maxItemCount=3`); it then clamps `ammoInClip` to the 12-round clip limit but adds the precomputed 700 rather than 12. `AddNewItem` can distribute stackable ammo across free inventory slots (`:3921-3968`).
- If `isFreeSlots` returns `-1`, the handler calls `ItemsDrop` with the original, not-yet-capped count, so a full inventory routes the same unchecked amount into a dropped item. The exact world-item representation/runtime consequences are not tested.
- The legitimate client path (`src_client/player/weapon.js:106-121`) returns its current weapon hash and clip count when weapon removal requests sendback. The server does not bind that callback to a pending server-side removal and no server-side maximum is checked before the inventory-space calculation. A direct remote can therefore request ammunition for a recognized weapon even without proving a loaded clip existed.

**Remediation (not implemented):** make ammo return an internal consequence of a server-owned weapon transition, bind it to the exact active weapon and one pending return, and derive the amount from authoritative state. At minimum reject counts outside `0..clipMax` before any inventory/drop side effect; do not use an overflow result from `isFreeSlots` as an insertion quantity; require successful, bounded inventory insertion and never drop a client-specified quantity. Add idempotency to prevent replay.

**Regression:** on disposable RAGE accounts, call `server.weapon.ammoin` directly with no weapon, a mismatched valid weapon hash, 0, -1, clipMax, clipMax+1, 1,000 and `int.MaxValue`. Repeat with empty, partly filled and full inventory. Compare every ammo item and world drop before/after; the only accepted amount must equal an actual server-authorized removed clip, once. Confirm ordinary draw/holster/switch/death/disconnect paths return exact ammo and retries do not duplicate. Static finding only; exploit runtime not reproduced.

## Additional examined boundaries

- `server.weapon.reload` consumes inventory ammo and sends a client give event. Negative values can produce a nonpositive computed `ammo`; `RemoveIndex` rejects `count <= 0`, but the remote still sends that amount to the client. Native behavior was not tested; reject negative and impossible clip values and revalidate on the server.
- `server.weapon.remove` only removes Ball/Snowball from the active fast slot; `changeweap` resolves the selected slot from server inventory and enforces character/arrest state for weapons. These narrow observations are not a full weapon policy review.
- No RAGE/client validation was possible. Audit of weapon damage/projectiles, weapon-shop purchase and all server/client ammo sync remains open.
