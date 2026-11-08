# Fraction stock and vehicle cargo review

Updated: 2026-11-08. Scope: `Main.ClientEvent_inputCallback` routes for `put_stock`, `take_stock`, `loadmats/unloadmats/loaddrugs/unloaddrugs/loadmedkits/unloadmedkits`; `Fractions.Manager.inputStocks` and `fracgarage`. Static source review only. No RAGE:MP, database, concurrency or restart tests were run.

## STOCK-001 — fraction stock and vehicle cargo transfers are not atomic

**Priority: High for stock/item integrity; runtime impact and exploitability depend on item repository behavior and concurrent state changes. Static evidence: confirmed unchecked operation results and mutation ordering.**

### Evidence

- `Main.cs:1788-1802` validates positive integer quantities for the six vehicle cargo callback names and delegates to `Stocks.fracgarage`. `Main.cs:1840-1853` validates positive quantities for `put_stock/take_stock` and delegates to `Stocks.inputStocks`.
- `Fractions/Manager.cs:2389-2468` (`put_stock`) increments faction material/drug/medkit stock before calling `Chars.Repository.Remove`; for money it increments `fractionData.Money` before calling `MoneySystem.Wallet.Change(player, -amount)`. The removal and wallet-change results are not verified, and no rollback is performed.
- `Fractions/Manager.cs:2471-2558` (`take_stock`) decrements faction stock before item creation or wallet credit. `AddNewItem` and `Wallet.Change` results are not checked; the method proceeds to logs/notifications as if the transfer succeeded.
- `Fractions/Manager.cs:2577-2745` (vehicle cargo load/unload paths) likewise mutates stock around `AddNewItem`/`Remove` calls without verifying the exact item quantity transferred. In load paths, faction stock is decremented after the item-add attempt without checking its return. In unload paths, the vehicle removal result is not available to the caller, while faction stock is increased.
- `Wallet.Change` returns `false` for missing character state, insufficient resulting cash, shutdown debit rejection, or exceptions (`MoneySystem/Wallet.cs:13-34`). `AddNewItem` returns a failure sentinel on some insertion failures; the stock-transfer callers discard the result.

### Impact / confidence

The code statically demonstrates that stock state and player/vehicle inventory are mutated as separate operations, with no confirmed exact-transfer contract or compensation. A failed/partial inventory mutation can leave faction stock and the corresponding inventory out of sync; a failed wallet mutation can leave faction money changed without the intended player debit/credit. The ordinary UI quantity validation does not make the sequence atomic. Actual failure frequency, concurrent exploitability, and persistence outcome require staging tests; this review does not claim a reproduced live exploit.

### Remediation

1. Introduce one stock-transfer service for character↔fraction and vehicle↔fraction transfers.
2. Validate ownership, fraction membership/rank, vehicle capability, current stock, inventory capacity and positive bounded quantity inside that service—not only in UI/open-menu paths.
3. Use exact-count consume/grant APIs. Do not change stock until the counterpart operation has succeeded; if a DB transaction cannot span both stores, persist a durable transfer intent/receipt and reconcile retries.
4. Make the operation idempotent with a unique transfer ID; prevent duplicate callbacks and concurrent overspending/overfilling with a lock or conditional DB update.
5. Check every return value and emit success logs/notifications only after settlement. Record failed/recovered transfers for audit.

### Regression matrix

- Character deposits/withdrawals for materials, drugs, medkits and cash; vehicle load/unload for each supported cargo type.
- Zero, negative, maximum, maximum+1, insufficient inventory/stock, full inventory/vehicle, and arithmetic boundaries.
- Force `AddNewItem` failure, partial `Remove`, wallet rejection, exception, DB outage and shutdown.
- Duplicate and concurrent callback submissions; disconnect/reconnect and process restart between each step.
- Assert conservation: player + vehicle + faction totals remain unchanged except for explicit configured sinks/sources; every transfer settles exactly once and success logs match committed balances.

### Related work

- `INV-003`: inventory slot-policy / direct-move paths that may affect where items can be consumed.
- `INV-009`: crafting count/remove location mismatch; similar class of non-atomic inventory consumption, but separate subsystem.
- `MONEY-030`: EventCoins aggregate-count vs inventory-only removal mismatch.
- `MONEY-034`: gang drug purchase arithmetic and ignored item-grant result.

**Status:** Open — static review documented; no patch, build, or runtime test.

## 2026-11-08 — cash stock settlement interim patch

Applied a narrow result-guard/order correction in both `Fractions.Manager.inputStocks` and `Organizations.Manager.inputStocks` for the `money` branches:

- `put_stock`: require `Wallet.Change(player, -amount)` to succeed before increasing faction/organization cash stock or emitting money logs.
- `take_stock`: require `Wallet.Change(player, amount)` to succeed before decreasing faction/organization cash stock or emitting money logs.

This prevents a rejected wallet mutation from changing the corresponding stock cash balance. The operations remain in-memory, separate and non-durable: a process crash or concurrent callbacks can still split or duplicate the two sides, and no transaction/receipt/lock was added. Item cargo branches remain unchanged; ignored `AddNewItem`/`Remove` results remain tracked under STOCK-001. No C# build, MySQL fault injection, concurrency or RAGE staging tests were run.

## STOCK-001 follow-up — organization stock and exact AddNewItem semantics

Current-branch revalidation also covered `Organizations.Manager.inputStocks`:

- Organization material/drug/medkit withdrawals decrement organization stock before calling `Chars.Repository.AddNewItem`; the return value is ignored, as in faction inventory withdrawal.
- `Chars.Repository.AddNewItem` returns `-1` on some failures, but can also return the last successful slot when its requested count is only partially inserted because available slots run out. A simple `result != -1` guard is therefore insufficient to prove full quantity delivery.
- `Chars.Repository.Remove` returns `void` and catches its own exceptions, so callers cannot currently confirm exact consumption or safe rollback through its public result.

No item/cargo patch was applied: correct remediation needs exact-count consume/grant APIs or a durable transfer intent with verified quantity delta and rollback/reconciliation. The four cash stock paths are now separately hardened under MONEY-035; STOCK-001 remains open for item and vehicle cargo.
