# Business ownership acquisition and player-to-player transfer — static review

Обновлено: 2026-11-08. Traced government business purchase and player-to-player business transfer from command/offer creation through confirmation, character BizIDs, owner mutation, wallet settlement and save calls. Static-only; no C# build, RAGE runtime or DB fault injection. No gameplay source changes.

## MONEY-043 — government business purchase commits ownership without confirming buyer debit

**Приоритет: высокий; unchecked debit and subsequent ownership commit statically confirmed; runtime failure window not reproduced.**

- `BusinessManager.buyBusinessCommand` validates the buyer's nearby business, government ownership, business limit and `UpdateData.CanIChange` before purchase (`Core/Businesses.cs:2971-3015`).
- It then calls `Wallet.Change(player, -biz.SellPrice)` at line 3021 but ignores the returned boolean. Regardless of the result, the method continues to log/report the purchase, clear all product stock, prune untaken orders, call `biz.SetOwner(player.Name)`, append the business ID to `characterData.BizIDs`, initialize the business bank balance and save the buyer's BizIDs (`:3021-3049`).
- `Wallet.Change` can return false for missing character data, insufficient resulting balance, server shutdown debit rejection or an exception (`MoneySystem/Wallet.cs:13-38`). The earlier `CanIChange` is only a preflight check and does not make the later debit atomic with ownership mutation.
- If the debit is rejected after preflight (for example, concurrent balance change or shutdown/failure path), the buyer can receive the business and the stock/order reset without a confirmed charge. The exact RAGE event timing and practical triggerability are not reproduced.

**Remediation (not implemented):** treat purchase as a durable idempotent settlement. Revalidate current government ownership and price, successfully reserve/debit buyer funds, then commit owner, BizIDs, stock/order reset and bank initialization; compensate or retain a retryable pending state if any later step fails. Do not log or notify success before commit. Add a unique purchase receipt and reconcile business Owner against character BizIDs on login.

## MONEY-044 — player-to-player business transfer ignores both wallet settlement results

**Приоритет: высокий; unchecked buyer debit/seller credit and ownership mutation statically confirmed; runtime failure not reproduced.**

- `sellBusinessCommand` creates a paired session offer with seller, price and business ID after checking proximity, seller ownership, buyer capacity and a cached buyer balance (`Core/Businesses.cs:3251-3327`).
- `acceptBuyBusiness` rechecks distance, buyer preflight funds, seller online state, seller BizIDs and current `biz.Owner`, and buyer business limit (`:3329-3396`). These checks are useful but do not settle money.
- The confirmation mutates and saves buyer BizIDs, removes and saves seller BizIDs, and changes `biz.Owner` before calling `Wallet.Change(player, -price)` and `Wallet.Change(target, price)` at lines 3398-3407. Neither boolean result is checked. It then logs and sends success notifications and clears both offers.
- If buyer debit fails, ownership can still transfer; if seller credit fails after buyer debit, the buyer pays but seller is not credited; if both fail, the business can still transfer without settlement. The two wallet operations and three ownership/list writes are separate and no durable shared transaction/receipt or compensation is visible.
- The offer is held in session state and the acceptance path does not show a unique settlement ID or explicit expiry/version binding. Duplicate/concurrent confirmation and disconnect timing need staging validation; this review does not claim they were reproduced.

**Remediation (not implemented):** use one unique, expiring transfer intent bound to business ID, buyer UUID, seller UUID, price and owner version. Settle buyer debit and seller credit atomically or through a durable state machine/outbox; commit owner and both BizIDs only after settlement is confirmed. Handle offline seller/buyer and partial DB writes, and make retries exactly-once. Do not clear or report success until the durable operation reaches a terminal state.

## Regression matrix

- MONEY-043: force `Wallet.Change=false` after preflight (balance race, shutdown gate, injected exception); assert no owner/BizIDs/stock/orders/bank mutation and no success log/notification.
- MONEY-043: duplicate purchase callback/command, concurrent purchase attempts, stale government owner state, business already privately owned, restart after each write boundary.
- MONEY-044: buyer debit false, seller credit false/exception, both false, DB failure saving buyer BizIDs, seller BizIDs or business Owner; assert either complete transfer and exact one-time settlement or no transfer.
- MONEY-044: duplicate dialog confirmation, simultaneous confirmations, offer replacement/expiry, seller disconnect/reconnect, buyer disconnect, changed owner/price and max-business boundary.
- Reconcile buyer/seller wallet balances, business Owner, both characters' BizIDs, bank/ledger rows, logs and receipt after restart.

## BUG-002 — admin business deletion removes the DB row before safely cleaning the owner/cache

**Приоритет: средний; offline-owner null path statically confirmed; runtime/admin workflow not reproduced.**

- deleteBusinessCommand executes DELETE FROM businesses first, then resolves the owner through NAPI.Player.GetPlayerFromName and immediately calls owner.GetCharacterData() without checking whether owner itself is null (Core/Businesses.cs:3180-3248).
- For an offline owner — including the government owner label when no such player is online — the lookup can return null and the dereference throws. The catch logs the exception, but execution never reaches biz.Destroy() or BizList.TryRemove. The DB row is already deleted, while the in-memory business remains until resource restart; the intended offline character BizIDs cleanup branch is unreachable for a null player object.
- This can leave runtime cache/world objects and character BizIDs inconsistent with the database. The exact RAGE return behavior of GetPlayerFromName should be confirmed on staging; source has no null guard.

## MONEY-047 — admin business deletion ignores the online owner's refund result

**Приоритет: средний; unchecked refund statically confirmed; runtime failure injection required.**

- In the online-owner branch, deleteBusinessCommand removes the business ID from ownerCharacterData.BizIDs and calls Wallet.Change(owner, biz.SellPrice) without checking the return value, then destroys/removes the business from runtime cache (Core/Businesses.cs:3237-3243).
- Wallet.Change can return false for a server-stop debit/credit policy path, missing/stale character state or exception (MoneySystem/Wallet.cs:13-38). If the credit fails, the business and BizID are removed but the owner receives no confirmed compensation; no pending refund receipt/retry is created.

**Remediation:** perform owner resolution before destructive DB mutation and explicitly branch online/offline/null; make DB business deletion, character BizIDs removal, refund and runtime cache removal one durable idempotent admin operation. Confirm refund before final delete or persist a pending compensation receipt. For offline owners, update the character by stable UUID in a checked transaction. Keep cache/world objects aligned with DB outcome.

**Regression:** delete government-owned and privately owned businesses with online/offline owners; inject null player lookup, missing character row, Wallet.Change=false/exception, SQL delete/update failure and crash between each write. Assert DB row, BizList, world shapes, owner BizIDs, wallet and refund receipt converge after restart.

## Updated scope boundary

These admin deletion observations are separate from MONEY-043/044 purchase/transfer settlement, MONEY-026 government sale, STOCK-002 retail stock and MONEY-040/041 tax/repossession. No gameplay source was modified.

## 2026-11-08 — bounded MONEY-044 acceptance preflight

A narrow patch was applied to `acceptBuyBusiness` in `Core/Businesses.cs`:

- Reject a missing pending offer, null seller reference or seller without active character data before dereferencing the seller.
- Require seller session and character data.
- Reject a nonpositive pending price and a business ID that is no longer present in `BizList`; clear both pending offer objects for these invalid states.

The core transfer is intentionally unchanged: buyer/seller BizIDs and `biz.Owner` are still mutated before two unchecked `Wallet.Change` calls. No naive reorder or compensating patch was applied because the subsequent ownership/BizIDs persistence APIs do not provide a durable transaction/commit result. MONEY-044 remains high/open.

## 2026-11-08 — MONEY-043 current-branch source revalidation

The current branch already contains an interim source guard in `buyBusinessCommand` (re-fetched from `Core/Businesses.cs`):

- Business bank balance initialization is attempted first through `Bank.SetBalance`; purchase aborts if it fails.
- The buyer debit is checked. If it rejects, the code attempts to restore the previous business bank balance and logs a failure if that compensation fails.
- Ownership, stock/order reset and buyer BizIDs mutation occur only after the wallet debit succeeds.

This is materially safer than the earlier static review text, which described the debit as unchecked. The finding remains open because bank initialization/debit/ownership/BizIDs are still separate in-memory/DB writes without one durable purchase receipt; a crash or later save failure can leave partial state. No C# build, RAGE staging or MySQL fault injection was run.
