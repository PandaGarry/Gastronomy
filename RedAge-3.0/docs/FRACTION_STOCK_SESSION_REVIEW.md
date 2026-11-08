# Fraction weapon stock session review

## INV-015 — stale OnFracStock allows reopening fraction stock outside its authorized interaction context

**Приоритет: высокий для целостности фракционного оружейного склада; статически подтверждён. Runtime reproduction не выполнялся.**

### Evidence

- Fraction interaction handlers in Fbi.cs, Sheriff.cs, Army.cs, Cityhall.cs and Police.cs set sessionData.OnFracStock to a fraction ID when the player enters the stock interaction. These entry flows check a mixture of faction identity, on-duty state, IsOpenGunStock and rank permission; exact checks vary by faction.
- SessionData.OnFracStock defaults to 0. A repository-wide code search found the five positive assignments and the property declaration, but no reset to 0 or other invalidation path.
- Fractions.Manager.Event_openWeaponsStock is a client RemoteEvent. For faction members it checks only that OnFracStock is nonzero and equals the player's current faction ID, then calls IsFractionAccess(OpenWeaponStock), then LoadOtherItemsData("Fraction", fracId, ...).
- IsFractionAccess checks current membership and rank/department access only; it does not enforce on-duty state, IsOpenGunStock, stock interaction proximity, dimension or a short-lived interaction token.
- Therefore, after a player has legitimately opened the faction stock once, the stale OnFracStock marker can allow a direct openWeaponStock remote from elsewhere while the player remains in that faction and retains the required rank—even after leaving the stock area, going off duty or the stock being closed. The generic ItemsMove/ItemsMoveStack/ItemsUse handlers then operate on the newly opened other container without repeating the entry ACL.
- This is a concrete faction-stock case of the broader INV-003 container-policy gap, not a new item mutation primitive.

### Impact boundary

The server-side remote gate is statically insufficient to prove current physical interaction, duty or stock-open state. A player must first have a valid OnFracStock value from an earlier stock interaction and still hold the rank permission. No remote call, weapon extraction or runtime impact has been reproduced.

### Remediation (not implemented)

- Replace OnFracStock as a durable session marker with a short-lived intent bound to player, fraction ID, exact stock, current faction membership/rank, on-duty state, stock-open state, position/dimension and expiry.
- Revalidate this intent in openWeaponStock and every generic item mutation affecting Fraction storage.
- Clear/revoke on auxiliary-pane close, full inventory close, leaving the interaction area/dimension, going off duty, faction/rank change, stock closure, timeout and disconnect.
- Recheck FractionData.IsOpenGunStock and all relevant role/duty rules in the remote itself; do not treat a stale integer as proof of current interaction.

### Regression matrix

- Open the stock legitimately once; move away, change dimension, go off duty and close the faction stock; direct openWeaponStock must reject in each case.
- Keep location but revoke rank, leave faction or change faction ID; reject and clear stale intent.
- Reopen legitimately while on duty and stock open; all supported factions (FIB, Sheriff, Army, City Hall, Police) retain intended access.
- After a valid open, move away/close stock/go off duty and direct-call inventory move, move.stack and use with other; reject with no cache/DB/item mutation.
- Replay openWeaponStock after close, disconnect/reconnect and session replacement; stale intent must not survive.
- Test Army separately because its initial interaction path differs in explicit rank checks; server-side permission policy must remain authoritative.

**Scope boundary:** INV-015 covers stale fraction-stock opening authorization. INV-003 remains the general server-side container/item-slot policy gap; INV-012..014 and VEH-012 remain separate vehicle/event cases.
