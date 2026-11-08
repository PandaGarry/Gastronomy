# Driving school payment settlement review

Date: 2026-11-08
Status: source patch applied; C# build and RAGE:MP regression tests pending.

## MONEY-050 — license grant before confirmed payment

### Source path
- `Core/DrivingSchool.cs`
- `startDrivingCourse(ExtPlayer player, int index)`
- Active license cases 0–5; purchase is reached from the server-owned driving-school popup callback.

### Evidence
Each active case previously performed `CanIChange`, then set `characterData.Licenses[index] = true` before calling `Wallet.Change(player, -Main.LicPrices[index])`. The bool result was ignored, and success notification followed regardless.

- Case 1 also advanced/completed the Zdobich quest before the debit.
- Cases 3–5 also credited `fractionData.Money` and wrote a money log after the unchecked debit.
- `Wallet.Change` can return false if the resulting balance is invalid, a debit is attempted during server shutdown, character data is missing, or an exception occurs. The preflight `CanIChange` does not guarantee the later debit succeeds.

This is a source-level settlement-ordering defect. No runtime reproduction is claimed.

### Patch applied
For each active case 0–5:
1. Retain the existing `CanIChange` preflight.
2. Require `Wallet.Change(player, -Main.LicPrices[index])` to return true; otherwise return immediately.
3. Only then grant the license and perform case-specific quest/faction-account/log/success side effects.

No changes were made to the commented-out old driving-course cases.

### Remaining considerations
- Wallet debit and license persistence are still separate in-memory/DB operations; this patch does not create a durable transaction or exactly-once receipt.
- Repeated/concurrent callbacks and disconnect/restart persistence require RAGE/MySQL validation.
- No new license-price cap was introduced; confirm configured `Main.LicPrices` are positive and within the wallet API's `int` range.

### Regression matrix
1. Purchase each license index 0–5 with sufficient balance: exact configured price debited once and the correct license granted.
2. Force `Wallet.Change` to return false or throw for each index: no license, quest progress, faction balance credit, money log or success notification.
3. Trigger the server-stopping debit rejection: no free license or side effect.
4. For case 1, verify quest stage/completion occurs only after successful payment.
5. For cases 3–5, verify faction money is credited only after successful debit.
6. Repeat the callback and test disconnect/reconnect/save behavior; no duplicate grant or payment.
7. Test insufficient funds and already-owned licenses; preserve existing user-facing behavior.

No C# build, RAGE runtime, MySQL fault injection or live exploit test has been run.
