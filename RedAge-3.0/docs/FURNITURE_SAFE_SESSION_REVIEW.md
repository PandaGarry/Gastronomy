# Furniture safe inventory session review

## INV-017 — furniture safe context remains mutable after leaving the house

**Приоритет: высокий для защиты house storage; stale context statically confirmed. Runtime reproduction not performed.**

### Evidence

- Core/Selecting.cs objectSelected validates that the selected object exists, is within 5m, the player has a current InsideHouseID and the corresponding house exists. It checks owner/roommate furniture permission or the burglary/lockpick path before opening the furniture container.
- The handler then calls LoadOtherItemsData with location furniture_<house.ID> and the selected furniture object ID.
- Houses/HouseManager.cs RemovePlayer (around :656-672), used by the ExitHouse interaction, moves the player outside, resets dimension and sets InsideHouseID = -1. It does not call ItemsClose or OtherClose and does not revoke the open furniture inventory context.
- Chars.Repository.ItemsMove, ItemsMoveStack and ItemsUse use the session's InventoryOtherLocationName for other-container operations. They do not revalidate current InsideHouseID, house owner/roommate permission, furniture object existence, distance or dimension. ItemsUse can transfer an item from other into the caller's character inventory.
- Thus a player who legitimately opened a furniture safe can leave the house and retain the server-side container location; direct generic inventory remotes can still attempt to mutate/extract from that furniture location.

### Impact boundary

The initial object/house/range and owner/roommate/burglary checks are real, but they are not repeated after exit. Static evidence establishes a stale container authorization path; actual item extraction and UI behavior require RAGE/MySQL staging. No live theft is claimed.

### Remediation (not implemented)

- Close/revoke furniture container context before HouseManager.RemovePlayer clears InsideHouseID; clear InventoryOtherLocationName and client other-pane state.
- Bind the open intent to player, exact house ID, furniture object ID/type, access mode (owner/roommate/burglary), dimension and expiry.
- Revalidate current house context, object existence, access policy and proximity on every move/stack/use/drop operation affecting furniture storage.
- Revoke on house exit, dimension change, object removal/replacement, roommate permission change, house ownership change, timeout and disconnect.

### Regression matrix

- Owner opens each safe type, exits house, then direct-calls inventory.move, move.stack and use with other; reject with no item/cache/DB mutation.
- Repeat as a furniture-authorized roommate and through the legitimate burglary/lockpick path; verify access mode cannot be upgraded or retained after exit.
- Remove/replace furniture object, revoke roommate furniture permission or transfer house ownership while the pane is open; stale operations reject.
- Test house exit while inventory is open, CEF-only close, repeated close and disconnect/reconnect.
- Verify valid in-house owner/roommate/burglary workflows still function and no items are lost on revocation.

**Scope boundary:** INV-017 is the furniture-safe post-exit case within INV-003. It is distinct from INV-016 organization stock exit and INV-012 vehicle trunk access.
