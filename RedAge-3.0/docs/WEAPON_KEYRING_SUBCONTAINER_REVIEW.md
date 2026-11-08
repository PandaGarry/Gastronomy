# Weapon attachments and key-ring subcontainers — static review

Обновлено: 2026-11-08. Narrow trace of parent-item opening, shared inventory remotes and parent-item movement. Static-only; no RAGE/MySQL runtime reproduction. No gameplay source patch.

## INV-019 — weapon/key-ring subcontainer session is not bound to current parent ownership

**Приоритет: средний; missing parent binding and stale-session mutation path statically confirmed; practical cross-owner extraction requires RAGE staging.**

- `Chars.Repository.ItemsUse` opens a weapon component container as `weapon_<Item.SqlId>` (around line 5406) and a key-ring container as `CarKey_<Item.SqlId>` (around lines 5600–5602).
- `LoadOtherItemsData` (line 2877) first closes the previous other pane, then stores only the constructed location string in `SessionData.InventoryOtherLocationName`. It does not store a parent item ID/type/owner/version or a revocable parent-item capability.
- `GetLocationName` (line 3371) resolves every `other` operation to that session string. `GetItemData` and `SetItemData` (lines 4733–4760) read/write the resolved container without checking that the parent weapon/keyring still exists in the caller's inventory or remains owned by the caller.
- The shared `server.gamemenu.inventory.move`, `move.stack` and `use` handlers in `Chars/Events.cs` (lines 191, 204, 217) dispatch directly to `ItemsMove`, `ItemsMoveStack` and `ItemsUse`. Those methods (lines 4882, 4933, 5305) use the mutable `other` location; no parent-item revalidation is performed. `SetItemData` has no `OtherClose` call or parent lookup.
- `ItemsUse` treats a selected item in `other` as a generic item retrieval into the caller's character inventory. Thus, if the parent item is moved, traded, dropped, deleted or replaced while the subcontainer remains open, the former holder can continue addressing the old `weapon_<SqlId>` / `CarKey_<SqlId>` storage. The source establishes the stale-context path; whether the client/UI or another lifecycle callback closes it in all practical sequences, and whether this yields cross-owner extraction in RAGE, must be reproduced on staging.

**Remediation (not implemented):** represent a parent subcontainer as a server-owned intent bound to player UUID, parent SqlId, parent type, allowed current owner-location(s), and a generation/version. Validate that the exact parent still exists and is owned by the caller on every move/stack/use/drop operation. Revoke/close the subcontainer whenever the parent leaves an authorized owner-controlled location, is traded/dropped/deleted/replaced, or the player disconnects. Ensure ownership transfer moves the container's authority with the parent, not with the previous viewer's session string.

**Regression matrix:**
- Open a weapon attachment pane, then move the parent weapon between inventory and fast slots; allow only explicitly supported owner-controlled locations.
- Open a weapon/key-ring pane, then trade, drop, transfer to vehicle/faction storage, delete, replace or otherwise change ownership of the parent; direct move, move.stack and use requests against `other` must be rejected after revocation.
- After parent transfer, verify the former holder cannot extract, alter or delete attachments/car keys; the new owner can open and use the same contents normally.
- Test parent removal and child mutation in the same tick, duplicate/replayed events, two viewers, disconnect/reconnect, SQL failure and restart. Assert no orphaned or duplicated child items.
- Verify legitimate component/key insertion, removal and key-ring use with a still-owned parent item.

## Scope and confidence

The source confirms that the session stores a location string and generic mutation endpoints do not revalidate parent ownership. No successful theft, item duplication or runtime exploit is claimed. Warehouse remains personal-UUID storage with an unresolved location-policy question; HeliCrash open/range lifecycle still needs staging confirmation and is separately covered in part by INV-018.
