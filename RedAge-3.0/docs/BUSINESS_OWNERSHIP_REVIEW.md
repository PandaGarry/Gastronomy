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

## Scope boundary

This pass covers government acquisition and player-to-player business ownership transfer only. Government sale payout/replay remains MONEY-026; retail stock settlement is STOCK-002; phone orders are MONEY-022/MONEY-025; business tax/repossessions are MONEY-040/041. These are not duplicated here.
