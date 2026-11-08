# Business hourly tax and repossession — static review

Обновлено: 2026-11-08. Traced business hourly tax, bank dirty-save worker, and the online/offline repossession branches. Static-only; no DB/RAGE runtime or fault injection.

## MONEY-040 — ordinary business tax debit is not marked dirty for bank persistence

**Приоритет: средний; persistence control-flow confirmed, restart behavior not reproduced.**

- Main.payDayTrigger calculates the business hourly tax, increments biz.Zatratq, then directly subtracts tax from Bank.Accounts[biz.BankID].Balance (Main.cs:4614-4638). On the ordinary solvent path it does not set bizBalance.IsSave=true or call Bank.SetSave.
- The bank worker selects only accounts with IsSave=true (Database/Models/Bank.cs:20-46). Bank.Save is the path that writes Balance to the DB and clears IsSave (MoneySystem/Bank.cs:150-175). Thus the normal tax debit is not scheduled for persistence by this path; a restart can restore the prior bank balance unless another operation independently marks the account dirty.
- The repossession branch later sets IsSave=true only after the balance becomes negative and is reset to zero. This does not repair the ordinary non-repossessing tax path.

**Remediation (not implemented):** use Bank.Change(biz.BankID, -tax) or explicitly mark the bank dirty only after validating the account and tax amount; ensure tax transfer to City Hall and business-bank debit share a durable transaction/receipt or reconciliation strategy.

**Regression:** payday with sufficient business funds; verify business bank debit and City Hall tax receipt both persist after worker flush and restart. Inject bank save failure/retry and duplicate payday handling; compare DB and in-memory balances.

## MONEY-041 — business tax repossession clears ownership without confirming owner compensation

**Приоритет: высокий; unchecked online/offline settlement statically confirmed, runtime failure not reproduced.**

- When hourly tax makes the business bank balance negative, the online-owner branch calls Wallet.Change(player, 80% of SellPrice) but ignores the boolean result, then removes the business ID from characterData.BizIDs. Afterward the code zeroes and marks the business bank dirty, clears the business owner and queues the business for save (Main.cs:4638-4685). A rejected/failed wallet credit therefore does not prevent repossession and loss of the business.
- For an offline owner, the code starts an asynchronous DB read/modify/write that adds compensation to characters.Money and removes the business ID from characters.Biz. The task logs exceptions but does not return a durable receipt/result to the caller; the outer payday flow still proceeds to zero the bank and clear the business owner. A DB error or crash can therefore leave the business repossessed without confirmed owner compensation.
- Online wallet, offline character DB update, business bank reset and business owner persistence are separate operations. No shared settlement ID, transaction or compensation/retry state is visible in this path.

**Remediation (not implemented):** represent tax repossession as a durable idempotent settlement with business ID, owner UUID, tax debt, compensation amount and state. Confirm owner compensation (online wallet or offline ledger) before final ownership release/bank reset, or retain a retryable pending repossession state. Reconcile owner BizIDs and business owner on login/restart.

**Regression:** online Wallet.Change=false/exception; offline character missing/DB update exception; crash between compensation and owner/bank save; duplicate payday/retry; negative bank balance and tax boundary. Assert compensation exactly once and no owner loss without durable settlement.

## Scope and confidence

Source ordering and worker dirty-save contract are statically visible. No runtime reproduction or production data inspection is claimed. Tax policy and repossession compensation semantics should be confirmed by the project owner before changing gameplay behavior.

## 2026-11-08 source reconciliation — MONEY-040 (partial)

The ordinary hourly business tax path has since been changed: `Main.payDayTrigger` now calls `Bank.ApplyBalanceAdjustment(biz.BankID, -tax, ...)` instead of directly mutating `Bank.Accounts[biz.BankID].Balance`. The helper performs checked arithmetic under `AccountSync`, increments the account revision and marks it dirty. The earlier missing-dirty-flag path described above is no longer present in the reviewed current branch. This source correction is static-only; DB save/restart tests remain pending.

**MONEY-041 remains open:** the online compensation result is ignored; offline compensation is asynchronous and unconfirmed before business ownership release/bank reset. In addition, the bank debit, City Hall/faction credits, owner compensation and ownership change are not one durable idempotent settlement. Do not mark business repossession fixed based only on the bank dirty-flag change.
