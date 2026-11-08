# Generic Main.cs input/dialog remotes — static review

Обновлено: 2026-11-07. Reviewed `inputCallback`, the mayor/fuel-control menu route, `syncWaypoint`, and selected generic `dialogCallback`/vehicle sync callsites in `Main.cs`. Static-only: no RAGE, CEF or MySQL runtime test. Findings below are mandatory remediation work, not accepted risks or confirmed runtime exploitation.

## MONEY-030 — festive-coin exchange can credit RedBucks without consuming coins

**Приоритет: высокий; count/remove location mismatch and RB credit order confirmed statically; direct-move→exchange chain requires RAGE proof.**

- `inputCallback` accepts the callback name and text from the client (`Main.cs:1503-1535`). In `sell_festive` (`:1891-1921`), it validates `3..500` coins and divisibility by three, then counts EventCoins across all character inventory sub-locations via `getCountItem(..., bagsToggled:false)`.
- It then calls `Chars.Repository.Remove(..., "inventory", EventCoins, limit)` without verifying that the requested amount was removed and immediately credits `limit / 3` RedBucks through `UpdateData.RedBucks`.
- `Remove` only examines the named `inventory` location (`Chars/Repository.cs:3410-3444`). If the event coins reside in `fastSlots` or another counted sub-location, the count check can pass while removal finds no coins; the RB credit still executes. Existing `INV-003` records that direct inventory-move remotes do not enforce all CEF slot restrictions. A direct move→`inputCallback("sell_festive", "3")` could therefore repeatedly exchange the same three coins for one RedBuck if the RAGE path permits the move. No reproduction or actual exploit is claimed.

**Remediation (not implemented):** validate and consume the exact quantity atomically from a single explicitly permitted location before credit; abort unless the consumed count equals the request. Prefer a transactional/idempotent exchange receipt and server-owned callback intent. Do not count from broader locations than the debit can consume.

**Regression:** on a disposable account, place event coins separately in inventory, fast slots and other character locations; direct-call the callback with 3, 498, 500, non-multiples, repeated calls and insufficient balances. Compare exact item/RedBuck balances and persistence after reconnect. Invalid or repeated exchange must not credit; valid exchange consumes exact coins exactly once. Static exploit chain depends on `INV-003` and requires RAGE staging.

## MONEY-031 — generic input callback bypasses mayor authorization for government fuel limits

**Приоритет: средний/высокий; missing authorization and persistent global state mutation statically confirmed; financial/gameplay impact requires staging.**

- `server.mayormenu.open` and `OpenFuelcontrolMenu` require the City Hall fraction leader (`Main.cs:5070-5075, 5120-5124`), and the normal UI callback is reachable through those gated menus.
- However, `inputCallback` accepts `fuelcontrol_city`, `fuelcontrol_police`, `fuelcontrol_ems`, `fuelcontrol_fib`, `fuelcontrol_army` and `fuelcontrol_news` without rechecking the sender's fraction or rank (`Main.cs:1544-1625`). Any authenticated character who passes the common session/account/character and non-Demorgan checks can submit a positive integer; there is no upper bound. The callback mutates `FractionData.FuelLimit` and may also clamp `FuelLeft`.
- `Fractions.Manager.SaveFractions` persists these fields; the daily reset copies `FuelLimit` into `FuelLeft` (`Main.cs:4800-4835`). Government refueling uses `FuelLeft` and debits the City Hall fraction balance (`Core/Businesses.cs:2908-2945`). An unauthorized large limit can therefore alter public fuel allocation, potentially across multiple government factions. Actual financial effect, worker ordering and balance policy were not exercised.

**Remediation (not implemented):** move authorization into the server-side setter; require City Hall leader/explicit authorized rank for the whole operation, use a server-owned target fraction and a documented maximum, and audit fuel-limit changes. Test ordinary leader/nonleader direct calls, every target fraction, over-limit integers, persistence/reconnect and daily reset/refuel accounting.

## MONEY-032 — mayor treasury withdrawal ignores bank-credit failure

**Приоритет: средний; unchecked result and treasury debit order confirmed statically; failure requires an invalid/stale bank account or exception and was not reproduced.**

- In `Main.cs:1665-1691`, `inputCallback("mayor_take", text)` correctly checks City Hall leader status, positive amount, `Cityhall.canGetMoney`, and treasury balance.
- It then calls `MoneySystem.Bank.Change(characterData.Bank, limit)` but ignores the returned `bool`, and unconditionally subtracts `limit` from `fractionData.Money`.
- `MoneySystem/Bank.cs:79-116` returns `false` when the bank account is missing or an exception occurs. In that failure path the City Hall treasury is still reduced although the personal bank was not credited. This is a conditional value-loss path, not an unauthorized withdrawal or a proven exploit.

**Remediation (not implemented):** require a successful bank credit before reducing treasury; preferably use a transactional transfer primitive with durable exactly-once receipt and compensating/retry semantics. If a single transaction is unavailable, persist an explicit pending transfer state and reconcile it on restart.

**Regression:** inject missing/stale bank account and bank-change exception; verify treasury and personal balance remain unchanged or are reconciled exactly once. Also test normal leader withdrawal, limit boundary, repeated callback and restart between each persistence step.

## MONEY-033 — ticket confirmation can pay out without a successful debit and can be replayed

**Приоритет: критичный для денежной целостности; both failure-to-abort and failure-to-consume ticket state confirmed statically; runtime exploitation not tested.**

- `FractionCommands.ticketConfirm(target, true)` reads `targetSessionData.TicketsData` into `ticketsData`, copies its target/price/reason, then executes `ticketsData = new TicketsData()`. This only replaces the local variable; it does not clear `targetSessionData.TicketsData`.
- It attempts `Wallet.Change(target, -sum)`, then `Bank.Change(targetCharacterData.Bank, -sum, false)` if the wallet debit fails. If both return false, the code sends error notifications but does not return. It continues to add 60% to the City Hall fraction and credits 40% to the issuing officer via `Wallet.Change(player, ...)`.
- The same still-populated ticket state can be submitted again through the `TICKET` dialog callback, so a repeated confirmation may re-run settlement while the state remains available. The normal client UI is not a server-side one-shot guarantee.
- The target/officer credits and fraction update are not wrapped in a durable transaction or idempotent settlement record. Exact persistence and online/offline behavior require staging.

**Remediation (not implemented):** atomically claim/consume the ticket intent before settlement; validate issuer/target/session and positive bounded sum; debit exactly once and abort if no debit succeeds; credit recipients only after confirmed debit; persist a unique ticket settlement ID and make retries idempotent. Clear the actual `targetSessionData.TicketsData` state in the same controlled transition. Consider a durable ledger/transaction rather than independent in-memory mutations.

**Regression:** test cash-only, bank-only, combined balances, insufficient total funds, invalid/stale issuer, issuer/target disconnect, duplicate direct TICKET callback, concurrent confirmations, and crash between debit/fraction/officer credits. Every ticket must settle at most once; no payout is allowed without exactly one successful debit; balances and logs must reconcile after restart.

## Waypoint relay — reviewed, no standalone issue asserted

`syncWaypoint` requires the sender to be a passenger in a vehicle with another character as driver, then relays client-provided X/Y and awards task 126. The relay itself performs the described passenger-to-driver waypoint transfer, so this static pass does not classify the client-supplied coordinates as a task bypass. Finite/world-bound validation and rate limiting still need staging/policy review; no coordinates were executed or tested.

## Other paths spot-checked / remaining scope

- `dialogCallback` has prior transaction findings documented separately (`VEH-001`, `VEH-006`, house/business/economy reviews); those paths remain open and are not repeated here.
- `syncSirenSound` contains server-side driver/faction checks. `VehStream_updateSirenStatus` is a separate client-supplied vehicle-entity sync path and needs a focused review; its normal client poll is currently commented out, so no runtime reachability claim is made here.
- `inputCallback` has many delegated callbacks (faction stock, transfers, tickets, leases, pet/tent and sale flows). Only listed branches were traced in this pass; authorization, numeric bounds, one-shot intent and persistence for all delegated handlers remain incomplete.
- No RAGE/DB assertions were executed. Continue the Main.cs and remote-event audit; do not treat this review as complete.


## Follow-up pass — complete inputCallback case inventory (2026-11-08)

Enumerated all 38 `case` occurrences (32 unique callback names) in `ClientEvent_inputCallback` (including six fuel-control aliases and their nested dispatch labels). This is a callback-label inventory, not a claim that every delegated implementation is fully audited.

### Delegated paths checked in this pass

- `player_medkit` → `FractionCommands.sellMedKitToTarget`: helper rechecks `RankToAccess.Medkit`, on-duty state, item availability, price range, proximity, target money and trade state. No additional standalone bypass asserted in this pass; purchase confirmation/settlement path remains part of the broader trade audit.
- `player_heal` → `FractionCommands.healTarget`: helper rechecks `RankToAccess.Heal`, on-duty state, price range, proximity and trade state, with vehicle/EMS checks in the vehicle branch. No additional standalone bypass asserted in this pass; downstream PAY_HEAL settlement still requires end-to-end confirmation.
- `mayor_put`: checks City Hall leader and bank debit result before increasing fraction treasury. This is materially safer than the inverse `mayor_take` flow recorded as MONEY-032.
- `player_ticketsum` / `player_ticketreason`: the originating selection path and `ticketToTarget` recheck ticket rank, on-duty status, amount ceiling and court-zone policy for City Hall. Confirmation settlement remains vulnerable as MONEY-033.

### Paths explicitly left open

- `club_setprice` → `AlcoFabrication.SetAlcoholPrice`: delegated role/rank, bounds, persistence and audit-log review pending.
- `player_offerhousesell` → `HouseManager.OfferHouseSell`: ownership, pending-offer replacement, amount ceiling, buyer/seller confirmation and durable settlement review pending.
- `buy_drugs` → `Gangs.BuyDrugs`: gang membership/rank, location, stock, amount bounds and cash/stock atomicity review pending.
- `loadmats/unloadmats/loaddrugs/unloaddrugs/loadmedkits/unloadmedkits` → `Stocks.fracgarage`: faction/rank, vehicle/warehouse location, capacity, stock accounting and persistence review pending.
- `put_stock/take_stock` → `Stocks.inputStocks`: container ownership, permission, quantity and save consistency review pending.
- `streetrace` → `StreetRace.SelectRate`: round lifecycle, bet bounds, duplicate submission, cancellation and settlement review pending.
- `sellcar`: offer creation has several ownership/distance/garage checks; buyer confirmation, atomic vehicle transfer/payment, stale ownership and duplicate/replay paths still require end-to-end tracing.
- `extend_hotel_rent` → `Houses.Hotel.ExtendHotelRent`: affordability, rent-time bounds, concurrency and persistence review pending.
- `rentname` / `sell_tent`: tent session/index and inventory-item provenance, stale selection, partial-stack movement, item-price mutation and persistence review pending.
- `make_ped_name` → `Pet.Repository.UpdateName`: pet ownership, selected-ped provenance and naming policy review pending.
- `weaptransfer`: branch currently validates an integer and returns without performing an action; determine whether it is dead legacy UI or an incomplete feature before removing/changing it.
- Generic callback argument array/string handling and all delegated callback rate limits remain to be reviewed systematically.

No additional issue ID was created from the helper checks above because the inspected code did not establish a new independent security defect. Existing MONEY-030..033 remain open. No runtime or build tests were run.


## MONEY-034 — integer overflow in gang drug purchase

**Приоритет: высокий; signed overflow and unchecked debit arithmetic statically confirmed; malformed inventory persistence/runtime effect requires staging.**

- `Main.ClientEvent_inputCallback` parses `buy_drugs` as a positive `int`, but has no meaningful upper bound before calling `Gangs.BuyDrugs(player, limit)`.
- `Gangs.BuyDrugs` checks `fractionData.Money < amount * Main.DrugsPrice` using unchecked `int` multiplication. The configured default `Main.DrugsPrice` is 30. For `amount = int.MaxValue`, the product wraps to `-30`; the insufficient-funds check therefore passes and `fractionData.Money -= amount * Main.DrugsPrice` increases the faction balance by 30 instead of charging it.
- The capacity guard also uses unchecked `count + amount`. If the vehicle already contains at least one drug item but is not full, this addition can overflow and bypass the configured capacity comparison.
- `Chars.Repository.AddNewItem` is called without checking its returned slot/result. Its stack merge path also adds `item.Count + count` using `int`; the huge amount can overflow again, so malformed/negative stack data or partial insertion is possible. The precise in-memory/DB result is not claimed without runtime verification.

**Remediation (not implemented):** enforce a small server-owned positive quantity ceiling before any arithmetic; use `checked` or `long` for total price and capacity calculations; validate `Main.DrugsPrice > 0`; calculate free capacity with subtraction after validating nonnegative operands; require `AddNewItem` to report the exact inserted quantity; only debit faction funds after a verified item grant, preferably via a transaction/ledger or compensating receipt. Reject requests during shutdown and audit the operation.

**Regression:** empty/partially filled/full vehicle; `1`, maximum allowed, max+1, `int.MaxValue`, `int.MinValue`, and boundary values around multiplication/addition overflow; insufficient faction balance; full inventory/slot exhaustion; AddNewItem partial failure; concurrent duplicate callbacks; verify no negative item counts, no capacity breach, no faction-balance increase, and exactly-once debit/grant after restart.



## MONEY-035 — faction cash withdrawal ignores wallet credit result

**Приоритет: высокий; debit-before-credit and ignored boolean statically confirmed.**

In both `Fractions.Manager.inputStocks` and `Organizations.Manager.inputStocks`, `take_stock` for `money` performs `fractionData.Money -= amount` and then calls `MoneySystem.Wallet.Change(player, amount)` without checking its boolean return. `Wallet.Change` can return false when the character is unavailable or its resulting integer balance is invalid/overflows (it computes `int temp = (int)characterData.Money + amount` and rejects `temp < 0`). The stock has already been debited; the code proceeds to logs/notifications. Thus the operation can lose faction funds without crediting the player. Normal boundary likelihood depends on the actual balance type/range and should be reproduced in staging; the unchecked failure path is proven by source.

**Remediation:** use a single transactional transfer/ledger operation with a checked wallet balance calculation; only commit the stock debit after a confirmed credit, or compensate atomically on failure. Handle concurrent withdrawals and exactly-once retries.

**Regression:** character missing/disconnecting, balance at/near numeric bounds, wallet update failure, concurrent withdrawals, duplicate callback, restart/reconciliation; assert faction debit equals player credit exactly once.

## STOCK-001 — faction stock debit ignores partial/failed inventory grant

**Приоритет: высокий; ignored return value and partial-grant semantics statically confirmed.**

- In `Fractions.Manager.inputStocks` and `Organizations.Manager.inputStocks` take paths, faction/organization stock counters are decremented before/around `Chars.Repository.AddNewItem`; its return value is ignored. `AddNewItem` returns `-1` when no slot is available and can return the last successful slot when it could not place the full requested quantity.
- Vehicle load paths (`load_mats`, `load_drugs`, `load_medkits`) similarly call `AddNewItem(null, vehicleInventory, ...)` and then subtract the full requested amount from faction stock. A check against aggregate item count/capacity does not prove that the vehicle inventory has enough free slots when other item types occupy slots. The medkit free-slot check is explicitly commented out.
- Therefore a failed or partial grant can still consume the full stock quantity. Runtime frequency and persisted DB outcome require disposable staging; the unchecked settlement path is confirmed.

**Remediation:** change inventory insertion API to return exact inserted count/result and make the operation atomic; reserve slots before stock debit, or roll back stock when insertion is incomplete; validate the actual inventory delta rather than aggregate count alone. Apply same contract to organization stock and other callers.

**Regression:** full/mixed vehicle inventory, fragmented stacks, zero free slots, partial insertion, SQL insert failure, concurrent loads, disconnect/restart; assert stock delta equals actual item delta and no item duplication/loss.

## Scope correction — negative quantities

The generic `Main.ClientEvent_inputCallback` branch for `put_stock`/`take_stock` parses the input and rejects `limit < 1` before calling `Stocks.inputStocks`. Therefore negative quantities are **not** recorded as a confirmed exploit through this entry point. Continue checking for alternate direct callers and retain server-side validation as a defense-in-depth requirement.

## Organization stock parity check

The corresponding `Organizations.Manager.inputStocks` implementation repeats both settlement defects: organization money is decremented before an unchecked `Wallet.Change`, and organization stock counters are decremented before an unchecked `AddNewItem` result. The deposit paths also mutate organization stock before invoking the wallet/item removal helpers without verifying their outcomes. The same atomicity/idempotency remediation must cover organization stock; do not treat this as a separate duplicate finding.


## MONEY-036 — Wallet.Change and persisted money width need one explicit contract

**Приоритет: низкий / latent type-contract risk; a reachable balance above Int32.MaxValue is not established.**

- `CharacterData.Money` is declared as `long` (`Character/Models/CharacterData.cs`).
- The generated `characters` DB model declares `money` as nullable `int(11)`. Character creation casts the configured initial balance to `int`; normal character save uses `Convert.ToInt32(characterData.Money)`; the money worker also writes `Convert.ToInt32(saveData[1])`.
- `Wallet.Change` computes `int temp = (int)characterData.Money + amount` and stores that int back into the long property. The previous example using a balance of 4,294,967,296 demonstrates the cast behavior mathematically, but that balance is not shown to be loadable or persistable under the current schema. No normal code path producing a persisted balance above Int32.MaxValue was found in this bounded pass.
- A positive credit at/near Int32.MaxValue can overflow the int addition and be rejected; this is relevant to settlement callers that ignore a false result (for example MONEY-035 and CAS-020), but it does not establish that Wallet.Change silently corrupts a valid DB-range balance.
- Treat this as a latent schema/type-contract inconsistency until a reachable >int producer is identified. Do not prioritize it as a current critical exploit.

**Remediation / decision:** choose one canonical contract. Either explicitly cap character cash at Int32.MaxValue and use checked arithmetic with clear rejection/compensation at the cap, or migrate the DB column, generated model, character create/save, money worker and wallet calculations together to BIGINT/long. Do not change only Wallet.Change.

**Regression:** test Int32.MaxValue-1, Int32.MaxValue and credits/debits crossing the cap; verify no wrap, no false success and correct caller compensation. Test DB save/reload round-trip at the selected maximum. If migrating to BIGINT, test values above Int32.MaxValue through create/load/save and every money worker.

## 2026-11-08 — faction/organization cash stock follow-up

The `put_stock` and `take_stock` cash branches were re-fetched and patched in both `Fractions/Manager.cs` and `Organizations/Manager.cs`: each branch now checks the corresponding `Wallet.Change` result before changing faction/organization cash stock or writing success logs. This closes the specific false-result ordering window for cash stock mutations. It does not make the transfer atomic, idempotent, crash-safe or concurrency-safe; item cargo exact-count transfer remains open as STOCK-001. Static-only; no build/RAGE/MySQL tests.

## 2026-11-08 — faction/organization cash stock follow-up

The `put_stock` and `take_stock` cash branches were re-fetched and patched in both `Fractions/Manager.cs` and `Organizations/Manager.cs`: each branch now checks the corresponding `Wallet.Change` result before changing faction/organization cash stock or writing success logs. This closes the specific false-result ordering window for cash stock mutations. It does not make the transfer atomic, idempotent, crash-safe or concurrency-safe; item cargo exact-count transfer remains open as STOCK-001. Static-only; no build/RAGE/MySQL tests.
