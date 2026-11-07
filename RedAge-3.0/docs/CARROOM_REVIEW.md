# Car showroom and test-drive remotes — static review

Обновлено: 2026-11-07. Traced `carroomBuy`, government autoroom purchase, donate autoroom purchase, cancel and `testDrive` through `Core/Carroom.cs`. Static-only: no RAGE vehicle spawn, wallet/DB failure injection or live inventory test. Findings require remediation; no code patch is included here.

## MONEY-029 — malformed showroom color is evaluated after payment

**Приоритет: средний; debit-before-unvalidated-dictionary-lookup is statically confirmed; runtime exception/reporting and post-failure state require RAGE staging.**

- `carroomBuy` takes `vName`, `color` and `id` directly from the client. In the personal purchase path it validates active showroom state, server-side product membership, funds and garage capacity, and may consume a business stock entry. It then calls `Wallet.Change(player, -prod.Price)` and only afterwards evaluates `carColors[color]` for `VehicleManager.Create` (`Core/Carroom.cs`, `RemoteEvent_carroomBuy`). A color not present in the server dictionary throws after debit; the outer catch logs it, and control does not reach the normal cancel/cleanup call. If business stock was consumed earlier, that mutation is also left behind.
- In the organization purchase path, after access/capacity/funds checks, it debits the player's wallet and then evaluates `carColors[color]` as an argument to `Organizations.Manager.CreateVehicle`. An invalid color can therefore leave the debit without creating the organization vehicle; the normal cancel path is skipped by the catch.
- `testDrive` similarly debits its fixed fee, changes dimension/position and creates a temporary vehicle before indexing `carColors[color]`. An invalid color can throw after charging and after entity creation but before assigning `sessionData.TestDriveVehicle` or starting its cleanup timer, creating a conditional orphan/stranded-player path. Exact cleanup/world behavior requires runtime testing.
- No server-side color allowlist validation is performed before the economic side effects in these paths. Client-side color choices do not constrain a direct remote caller.

**Remediation (not implemented):** validate `color` using `carColors.ContainsKey` and validate model/catalog/context before charge, stock reservation or dimension changes. Stage purchases as a transactional operation: reserve funds and stock, create vehicle, then commit, with compensation on any failure; ensure temporary test-drive creation has cleanup and return-to-origin in `finally`/failure paths. Check and handle Wallet/RedBucks/vehicle-create results.

**Regression:** on disposable accounts, call `carroomBuy` with valid showroom/product and invalid/empty color for personal and organization purchase; assert balance, business stock, organization fleet, player dimension and session selection remain unchanged or the exact purchase succeeds. Test each supported color and valid model as controls. Call `testDrive` with invalid color, unknown/noncatalog valid vehicle model, `type` values 0/1/2/255, and creation failure; assert no charge without a tracked/cleaned vehicle, no orphan entity, and player returns to the original position/dimension. Static only; no RAGE/DB test performed.

## Additional boundary observations

- Personal showroom purchase checks `TempBizID`, business product name and `UpdateData.CanIChange`; organization purchase checks `OrgBuyCars` and fleet capacity. These checks do not replace validation of every remote argument before payment.
- `testDrive` has no explicit active-showroom (`TempBizID`) or server-side model allowlist check in the inspected handler; whether noncatalog test drives are intended is a product-policy question. This remains a review item rather than a separately asserted exploit.
- Existing vehicle purchase/sale, garage and organization issues remain open in their respective review files. This pass is not a complete vehicle or business review.
