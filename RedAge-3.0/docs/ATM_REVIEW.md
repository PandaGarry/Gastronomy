# ATM remotes — static review

Обновлено: 2026-11-07. Traced the ATM interaction and `atmCB` → `atmVal` server events, including house-account deposit selection. This is a narrow cash ATM slice, not a full bank/transfer review. No build, RAGE staging or policy confirmation.

## MONEY-004 — ATM withdrawal remote lacks server-side location and eligibility checks

**Приоритет: низкий/средний; policy-dependent, static path confirmed, runtime untested.**

- The intended entry point is the ATM interaction `OnAtm`, which checks demorgan state, wanted status and the player's bank account before opening the UI (`MoneySystem/Bank.cs:410-430`).
- The subsequent `[RemoteEvent("atmCB")]` handler accepts client-supplied type/index and sets `sessionData.ATMData.Type=1` for withdrawal (`:793-855`). It has no check that the player is near an ATM, has an active server-issued ATM interaction, is not wanted/in demorgan, or has not left the ATM.
- `[RemoteEvent("atmVal")]` trusts that session type (`:469-489`). For type 1 it debits the caller's own bank account and credits their wallet (`:507-520`); it does not re-check proximity, wanted status, demorgan or an active ATM session. The two remotes can therefore be called directly in sequence to withdraw cash away from an ATM and bypass the eligibility checks in `OnAtm`. The source path uses the caller's own account; no cross-player bank withdrawal was found in this branch.

**Remediation (not implemented):** bind menu/action to a short-lived, one-shot server ATM intent with ATM identity/location; re-check distance, wanted/demorgan and account eligibility on every withdrawal; consume the intent after the transaction.

**Regression:** normal ATM withdraw/deposit; direct `atmCB(type=1,index=1)` + `atmVal` far from all ATMs; leave range between menu and amount; wanted/demorgan player; no account, malformed amount, repeated callbacks and server stopping. Verify rejected attempts leave both balances unchanged and legitimate ATM use remains functional. Requires RAGE staging and owner confirmation of the policy.

## House-account selection boundary

The ATM menu's house-account branch separately requires `HouseManager.GetHouse(player, true)` (`Bank.cs:825-856`), and the house deposit path re-checks owner-only house access before changing the house bank balance (`:522-569`). This does not repair the general ATM proximity/eligibility gap. The broader issue record remains `ECONOMY_REVIEW.md` (`MONEY-004`). House tax persistence/repossessions are covered in `PROPERTY_TAX_REVIEW.md` (`MONEY-019`, `PROP-003`).


## MONEY-053 — cash ATM and house deposit ignore the second settlement leg

**Приоритет: средний; static ordering confirmed, runtime failure path not reproduced.**

The current branch `MoneySystem/Bank.cs` contains four related two-leg cash flows in `ClientEvent_ATMVAL`:

- Regular cash deposit (`type == 0`): `Wallet.Change(player, -myamount)` is checked, but `Bank.Change(characterData.Bank, +myamount)` is ignored. The handler still plays the success sound and writes the ATM-in log. If the bank credit returns false (e.g. account disappeared or an exception occurs before mutation), the wallet debit remains applied without a matching bank credit.
- Regular cash withdrawal (`type == 1`): `Bank.Change(characterData.Bank, -myamount)` is checked, but `Wallet.Change(player, +myamount)` is ignored. The handler still logs the ATM-out flow after a rejected wallet credit; the bank debit may remain without cash received.
- House deposit (`type == 2`): wallet debit is checked, but the house-bank credit result is ignored; the handler logs and reports the deposit regardless.
- Business deposit (`type == 3`): the same unchecked bank-credit leg is already separately tracked as MONEY-039; keep that issue as the canonical business-specific record and do not duplicate it here.

`Wallet.Change` in the current branch tracks whether the in-memory balance was mutated and catches notification exceptions separately, so a false result should represent a rejected/unapplied wallet mutation under the reviewed flow. `Bank.Change` similarly isolates notification failures after its locked mutation. Nevertheless, these pairs are not one DB transaction: process failure between legs or failed compensation can still leave partial settlement. Do not retry the original leg blindly.

**Remediation:** introduce one idempotent cash↔bank settlement operation that validates both accounts and resulting ranges, mutates both sides under a single settlement boundary, marks both dirty, and records a durable receipt/ledger transaction before reporting success. As a bounded interim fix, require the second leg to succeed and attempt a checked compensation of the first leg; log and surface any compensation failure, while keeping the issue open until durable transaction/restart tests pass. Keep client notifications and GameLog after settlement.

**Regression:** normal deposit/withdrawal; missing bank account after UI opened; force Bank.Change false after wallet debit; force Wallet.Change false after bank debit; compensation success/failure; DB failure/restart between legs; duplicate/concurrent ATM submissions; insufficient cash/bank; near wallet/bank INT limits; verify no success log/sound/UI update before confirmed settlement and exactly one net delta on both balances. Requires disposable MySQL and RAGE staging.
