# Pet-shop remote authorization and purchase lifecycle — static review

Обновлено: 2026-11-08. Traced business interaction, pet-shop CEF/client event, server purchase remote, stock helper, house state and client pet creation. Static-only; RAGE/CEF runtime and DB fault injection were not performed.

## PET-001 — petshopBuy accepts stale business context and unvalidated pet model

**Приоритет: средний/высокий; missing server-side context checks, early teleport and reusable TempBizID are statically confirmed; arbitrary model-string behavior requires staging.**

- OnBusinessAction assigns SessionData.BizID for every business interaction and sets TempBizID for several non-pet business types, including showrooms, gun shop, clothes and masks (Core/Businesses.cs:1036 onward). enterPetShop uses the current TempBizID and opens the client pet shop (1227-1251).
- The client buyPet handler sends pet.model to the server as petshopBuy (src_client/player/petshop.js:87-97). The server handler checks only that TempBizID is nonnegative and resolves to a business (Core/Businesses.cs:1253-1261). It does not require biz.Type == 14, an active server-issued pet-shop session, proximity, matching dimension or an unexpired one-shot intent.
- Before validating house eligibility or purchase details, the handler teleports the player to the selected business' EnterPoint and resets dimension to 0 (1261-1264). A direct call with stale TempBizID can therefore trigger a server-side teleport even when the caller has no eligible house.
- The handler never clears TempBizID after a successful purchase. The only inspected reset is in petshopCancel (1299-1312), so the purchase remote can be replayed after the client UI closes and can overwrite the selected pet repeatedly.
- petName is not checked against the server allowlist PetNames (lines 447-457). The value is saved to house.PetName and characterData.PetName (1280-1286). When the house is sent to a client, HouseManager forwards that string in petinhouse; the client maps known names to hashes but its switch has no rejecting default and passes unknown values to mp.peds.new (src_client/index.js, petinhouse handler). Exact RAGE behavior for arbitrary model strings is not verified.
- takeProd returns true if no matching product is found (Core/Businesses.cs:1918-1945; STOCK-002). Because the handler trusts any business in TempBizID, a non-pet business may not contain Корм для животных; the purchase can pass the stock gate without reserving pet food. Wallet.Change is also unchecked here and the purchase's house/character mutations follow it. These settlement defects are cross-referenced to STOCK-002 rather than duplicated as separate findings.

**Impact:** direct/replayed remote calls can act outside a live pet-shop interaction, use a stale non-pet business context, trigger an early teleport, and persist a pet name that was never offered by the server. Whether an unknown model string can create an unintended ped or only causes a client-side error must be established in staging.

**Remediation (not implemented):** create a short-lived, one-shot server-side pet purchase intent only when entering a Type==14 business. Bind it to player, business ID, position, dimension, expiry and expected price; revalidate all fields on purchase. Accept only exact values from the server PetNames allowlist (prefer a stable enum/model ID over a client string). Validate house/pet eligibility and stock before any teleport or mutation. Settle wallet, business stock/revenue and house/character pet state exactly once; only then send success/teleport as required. Consume and clear the intent on success, cancel, timeout, disconnect and context change. Reject missing products through the shared stock service.

## Regression matrix

- Directly invoke petshopBuy with no previous business interaction: no teleport, money, stock, house or character mutation.
- Interact with a non-pet business that sets TempBizID, leave it, then invoke petshopBuy: reject without side effects.
- Enter a Type==14 pet shop, leave range/change dimension/vehicle/context, then invoke: reject.
- Replay the same valid petshopBuy event after success and concurrently: at most one purchase/house mutation and one charge.
- Test all nine allowed pet names and arbitrary/empty/oversized strings; unknown values must not reach the client model constructor or persistence.
- No house, type-7 house and house without PetPosition: reject before teleport or charge.
- Missing pet-food product, zero/negative price, empty stock, failed owner-bank credit and failed customer wallet debit: no partial purchase; reconcile stock and balances.
- Disconnect/reconnect and restart after each settlement boundary; verify durable house/character pet state and exactly-once charge.

## Scope boundary

PET-001 is separate from VEH-009 (petrol remote uses stale BizID) and STOCK-002 (shared stock/customer settlement flaws). This review records pet-shop-specific session authorization, teleport ordering, replay and model allowlist validation.
