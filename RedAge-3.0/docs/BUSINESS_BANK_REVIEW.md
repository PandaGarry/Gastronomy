# Business bank account operations — static review

Обновлено: 2026-11-08. Narrow trace of ATM business-account deposit selection and settlement. Static-only; no RAGE/DB failure injection.

## MONEY-039 — ATM business deposit debits the player before checking the business-bank credit

**Приоритет: средний; unchecked settlement result statically confirmed, runtime failure not reproduced.**

- ATM business-account selection is handled by atmCB case 3. It resolves the selected business through characterData.BizIDs[index] and stores the index in sessionData.ATMData.BizID (MoneySystem/Bank.cs:878-917).
- atmVal case 3 resolves that business again, calculates the deposit cap, debits the player's wallet with Wallet.Change(player, -myamount), then calls Bank.Change(biz.BankID, +myamount) without checking the boolean result. It proceeds to money log, bank success message and UI refresh regardless of whether the business account was credited (Bank.cs:596-657).
- Bank.Change returns false if the business account is absent or an exception occurs (MoneySystem/Bank.cs:79-120). It also rejects an invalid resulting balance. Thus a player debit can be accepted while the target business-bank credit fails, with no compensation or pending receipt.
- The selection path also trusts the index into BizIDs and relies on the stored session type; bounds and owner reconciliation are not repeated at atmVal. This is an adjacent robustness/authorization boundary; the direct demonstrated integrity issue is the unchecked second leg of the deposit.
- The general ATM remote also lacks a server-side active-location/eligibility intent (`MONEY-004`, `ATM_REVIEW.md`); this review does not duplicate that finding.

**Remediation (not implemented):** settle the player debit and business-account credit atomically or through a durable idempotent transfer receipt. Require Bank.Change success before logging/reporting success; if the second leg fails, refund the player or retain a retryable pending deposit. Revalidate the selected BizID against authoritative current ownership and validate the index/type at the final event.

**Regression:** inject missing business account, Bank.Change false/exception and balance-boundary failure after successful Wallet.Change; assert player balance is restored or pending receipt is durable, business balance and log agree, and duplicate atmVal cannot repeat. Test stale BizIDs, negative/zero/int boundary amounts, invalid index, replay and far-from-ATM direct remotes on disposable RAGE/MySQL staging.

## Scope and confidence

Static source ordering and return contract confirmed. No live exploit, DB failure or runtime reproduction claimed.