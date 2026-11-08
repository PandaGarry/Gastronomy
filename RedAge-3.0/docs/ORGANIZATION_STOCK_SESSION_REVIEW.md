# Organization stock session review

## INV-016 — organization stock remains mutable after leaving the organization interior

**Приоритет: высокий для целостности organization stock; stale container context statically confirmed. Runtime reproduction not performed.**

### Evidence

- Organizations.Manager.OpenWeaponStock (around :1736-1755) checks that the character has an organization, that the organization is active and its stock is open, and that organizationData.Id equals characterData.InsideOrganizationID. It then calls LoadOtherItemsData for Organization_<organization ID>.
- Organizations.Manager.RemovePlayer (around :2211-2221) moves the player outside, resets the dimension and sets characterData.InsideOrganizationID = -1. The method does not call ItemsClose or OtherClose and does not revoke the open organization inventory context.
- Chars.Repository.LoadOtherItemsData stores only InventoryOtherLocationName. The generic server inventory remotes call ItemsMove, ItemsMoveStack and ItemsUse; these methods do not revalidate InsideOrganizationID, organization membership/rank, stock-open state, current dimension or physical location before mutating the other container.
- ItemsMoveStack and ItemsUse only apply the special foreign-tent read-only guard; Organization storage is not covered by that guard.
- Therefore, after legitimately opening an organization stock and then leaving the organization interior through RemovePlayer, the old Organization_<ID> context can remain in session and generic item remotes can still attempt to move/use items from it. The initial InsideOrganizationID check protects opening, not later mutations.

### Impact boundary

Static code establishes that the organization exit method clears the interior marker without closing/revoking the inventory context, while generic mutation methods do not recheck the marker. Whether the CEF UI closes automatically on every exit path does not provide server-side authorization: direct remotes remain callable. No item extraction or runtime impact has been reproduced.

### Remediation (not implemented)

- Revoke and close Organization inventory context before/when leaving the organization interior; clear InventoryOtherLocationName and IsOrgStockActive.
- Bind the container intent to player, organization ID, current organization membership/rank, stock-open state, dimension/interior and expiry.
- Revalidate that intent on every move/stack/use/drop endpoint that reads or writes Organization storage.
- Make exit, organization removal, stock closure, dimension change, disconnect and organization deletion revoke the intent idempotently.

### Regression matrix

- Open organization weapon stock, exit through RemovePlayer and direct-call move/move.stack/use with other; all must reject with no item/cache/DB mutation.
- Repeat after organization membership removal, rank/access revocation, stock closure and organization deactivation.
- Verify valid member in active organization interior can still access intended stock; test normal and weapon-stock containers separately.
- Try remote calls after CEF closes, after client disconnect/reconnect and after switching to another other-container; stale Organization location must not survive.
- Test concurrent exit and item mutation; the exit/revoke must win or serialize safely, with no partial item transfer.

**Scope boundary:** INV-016 is the organization-stock post-exit case within the broader INV-003 container policy gap. Fraction stock stale-open authorization is INV-015; vehicle/event containers remain INV-012..014.
