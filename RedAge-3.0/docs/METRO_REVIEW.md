# Metro ticket purchase review

Date: 2026-11-08
Status: source patch applied; C# build and RAGE:MP regression tests pending.

## MONEY-049 — unchecked ticket count arithmetic and debit result

### Source path
- `Events/Metro.cs` — `Metro.OnBuyTicket(ExtPlayer player, string station, int Increase)`
- Remote: `metro.server.buyTicket`
- Wallet contract: `MoneySystem/Wallet.cs` — `Wallet.Change` returns `false` for missing character data, negative resulting balance, server-stop debit rejection, or caught exceptions.

### Evidence and impact
Before the patch, the server calculated `int totalprice = PriceTicket * Increase` using client-controlled `Increase`. The multiplication was unchecked and could wrap. It then called `Wallet.Change(player, -totalprice)` but ignored the result, wrote a money log, sent the success event and changed the player's dimension regardless.

A false wallet result therefore did not stop the purchase side effects. This is a source-level correctness issue; no successful live exploit or runtime failure has been reproduced.

### Patch applied
- Widen multiplication before it occurs: `long calculatedPrice = (long)PriceTicket * Increase`.
- Reject values below 1 or above `int.MaxValue`, because Wallet.Change currently accepts `int`.
- Call `Wallet.Change` and abort if it returns false.
- Only after successful debit write the money log, send success and change dimension.

### Remaining risks / policy
- This patch does not introduce a maximum ticket count beyond the representable wallet API range. Confirm whether product policy requires a lower per-purchase cap.
- The client-supplied station label is still passed to the success event/log; verify the CEF uses it only as a display/route identifier and does not treat it as an authoritative destination.
- The wallet debit and dimension transition are not a durable transaction. If the process fails after debit but before the success event, the player may be charged without completing the trip. A durable receipt/refund mechanism would be needed for strict exactly-once travel.

### Regression matrix
1. `Increase` = negative, zero: no debit, log, success event or dimension change.
2. `Increase` = 1 and a normal supported value: exactly `PriceTicket * Increase` debited once; success follows.
3. `Increase` = `int.MaxValue` and `int.MinValue`: no arithmetic wrap or unintended credit; out-of-range request rejected.
4. Force `Wallet.Change` to return false / throw: no money log, success event or dimension change.
5. Race with server stopping: rejected debit must not produce a ticket success.
6. Disconnect/crash between debit and success: document expected refund/receipt behavior.

No C# build, RAGE runtime, MySQL fault injection or live exploit test has been run.
