# Auto-mechanic repair and fuel-service settlement — static review

Обновлено: 2026-11-08. Revalidated current branch source for mechanic repair offer/acceptance, mechanic fuel purchase from a gas station, and mechanic-to-customer fuel offer/acceptance. Static-only; no C# build, RAGE runtime or wallet failure injection. No gameplay patch applied in this pass: a safe fix requires durable service intent/settlement semantics, not a local bool check.

## JOB-005 — mechanic service effects proceed without confirmed two-sided wallet settlement

**Приоритет: высокий; unchecked settlement results and effect ordering statically confirmed; runtime failure paths not reproduced.**

- mechanicPay reads the buyer's session offer, checks buyer funds through CanIChange, repairs and repositions the buyer's current vehicle, then calls Wallet.Change(buyer, -price) and Wallet.Change(mechanic, price) without checking either result (Jobs/AutoMechanic.cs:137-181). It logs and notifies success, clears both offer states and advances mechanic quest/skill progress regardless of the wallet results.
- mechanicPayFuel similarly checks a preflight buyer balance, validates that the mechanic remains in a work vehicle with enough loaded fuel, then calls both Wallet.Change operations without checking results. It logs success and transfers fuel to the buyer's current vehicle, decreases the mechanic's loaded fuel and clears offer state regardless of whether buyer debit and mechanic credit succeeded (Jobs/AutoMechanic.cs:376-466).
- Wallet.Change can return false for missing/stale character state, insufficient resulting balance, server-stop debit rejection or exceptions (MoneySystem/Wallet.cs:13-38). A preflight balance check is not atomic with the later two-wallet settlement.
- If buyer debit fails but mechanic credit succeeds, the repair/fuel can be delivered without payment and the mechanic still receives proceeds. If buyer debit succeeds but mechanic credit fails, the buyer pays while the mechanic receives nothing; the repair/fuel still proceeds. There is no shared transaction, settlement ID, pending receipt or compensation path in these methods.
- The mechanic's own gas-station fuel purchase, buyFuel, calls takeProd and then ignores Wallet.Change(player, -amount) before increasing the mechanic vehicle's VehLoadedFuel (Jobs/AutoMechanic.cs:221-282). This is an additional unchecked purchase callsite; common takeProd stock/bank ordering is tracked separately as STOCK-002.
- mechanicRepair validates the offer-time proximity, mechanic work status and fixed price, but mechanicPay does not revalidate the original target vehicle identity, offer age or proximity at acceptance. mechanicPayFuel also does not revalidate the offer-time distance. Treat these as stale-offer/context test requirements rather than asserting a separate theft/exploit without RAGE staging.

**Remediation (not implemented):** create a unique, expiring service intent bound to buyer UUID, mechanic UUID, service type, price/quantity and vehicle identity. Revalidate both players, work status, vehicle and offer state at acceptance. Use durable escrow/atomic ledger or a state machine that confirms buyer debit and mechanic credit before repair/fuel transfer; compensate or retain retryable pending state on partial failure. For buyFuel, debit successfully before committing the mechanic's fuel reserve, with exact stock/revenue rollback if either leg fails. Progress, logs and success notifications must occur only after terminal settlement.

## Regression matrix

- mechanicPay: buyer Wallet.Change=false/exception, mechanic Wallet.Change=false/exception, both false; assert no repair, quest progress, success notification or log unless exact settlement is committed.
- mechanicPayFuel: buyer debit failure, mechanic credit failure, insufficient mechanic fuel, disconnect/reconnect and partial wallet persistence; assert buyer/mechanic balances and both vehicles' fuel reserves remain consistent.
- buyFuel: wallet debit false after takeProd/owner credit; assert mechanic VehLoadedFuel is not increased for free and business stock/revenue are reconciled.
- Replay/duplicate generic dialogCallback, expired/replaced offer, wrong buyer, mechanic off duty, work vehicle replaced, buyer vehicle swapped, movement beyond offer radius, and concurrent accept/cancel.
- Restart/fault injection between buyer debit, mechanic credit, vehicle repair/fuel mutation and offer cleanup; prove exactly-once service and ledger consistency.

## Scope boundary

JOB-005 covers mechanic repair/fuel service settlement. JOB-004 is Trucker payout; STOCK-002 covers shared business takeProd and retail stock settlement; VEH-009 covers the separate petrol station context authorization issue. No gameplay source was modified.
 
## 2026-11-08 follow-up — patch decision

Re-fetched `AutoMechanic.cs` from `redage/audit-continuation` and reconfirmed all three acceptance/purchase paths remain unchanged: `mechanicPay` mutates vehicle repair state before two unchecked wallet calls; `mechanicPayFuel` performs two unchecked wallet calls before fuel transfer; `buyFuel` calls `BusinessManager.takeProd` before unchecked wallet debit and then increases `VehLoadedFuel`. A naive `if (!Wallet.Change(...)) return` is insufficient: for player-to-player services the first leg can succeed while the second fails, and for station fuel the stock/revenue leg may already have committed. Reordering alone also creates an unpaid-stock or paid-without-fuel failure window.

**Decision:** leave source unchanged until a shared atomic/durable settlement API exists. Required design: one-shot expiring service intent bound to both UUIDs, exact vehicle identity, amount/quantity and offer revision; revalidate context at acceptance; durable receipt/escrow for both wallets; commit vehicle repair/fuel and stock mutation only against that receipt; recover/reconcile after restart; only then progress quests/skills and emit success. This avoids unsafe refund loops and false assumptions that `Wallet.Change(true)` means DB durability.
