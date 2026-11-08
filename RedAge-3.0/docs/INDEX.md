# Документация RedAge 3.0

Обновлено: 2026-11-07. Источник: commit `23730b8cd464f86c47eaae6f80d182cd651092b2`; рабочая копия частичная. В `SOURCE_SNAPSHOT.md` указаны границы и локально очищенные конфиги.

## Текущий статус

- Аудит продолжается; в inventory, Roulette и Blackjack внесены узкие local hardening patches, но они пока не скомпилированы и не проверены в RAGE staging. NewCasino Roulette/Blackjack/Spin/Horses/LuckyWheel имеют только частичные статические reviews; ставки, settlement, RNG и prize-grant paths требуют further review/runtime tests.
- Client JS bundle собран в изолированной копии.
- CEF build и C# build заблокированы текущими ограничениями toolchain/RAM.
- SQL import/RAGE smoke tests ожидают одноразовую test DB и полный runtime/assets.
- Найдены и локально очищены credential-bearing значения; если они были активны, владельцу нужно их ротировать.
- Auth review выявил legacy password hash без соли; миграция не выполнена, требуется отдельный backward-compatible план.
- Economy/payment review зарегистрировал RedBucks debit/credit, deferred persistence, transfer replay, ATM validation, external receipt idempotency, DonatePack intent risks и roulette negative-count/overflow credit path. Для roulette внесены только узкие input guards; все такие изменения ещё требуют build/staging tests.
- Casino coverage расширено legacy `/dice` и Lottery (`CAS-020..026`): findings статические, исходники не менялись, деньги/прогрессия требуют policy review и DB/RAGE regression testing.
- BattlePass progression review начат: CAS-027..028 охватывают reward receipt crash/replay и failure/partial grant. В `UpdateReward` trace найдено 209 non-comment invocation lines, включая 72 для IDs вне текущего Season4 catalog; inventory пока не равен полному аудиту producers.
- Sapper minigame: `MONEY-008..009` — критические статические findings по отрицательной ставке (RB mint), client-controlled outcome/multiplier и loss refund; `PROG-001` — progress-before-session-validation. Подробности: `SAPPER_REVIEW.md`.
- Quest progression: `PROG-002..004` фиксируют direct clear task bypass, client-forgeable Dada/Edward objective flags и admin SkipQuest recipient bug; `BUG-001` — disconnected legacy quest dispatch (active runtime scope не подтверждён); `INV-008` — Granny Bear item injection. Проход частичный; см. `QUESTS_REVIEW.md`.
- Wedding remote: `MONEY-010` — divorce fee may be debited before failed offline-spouse unlink after disconnect race; `WEDDING-001` — null target dereference on invalid input. Статический анализ, runtime policy/tests pending; `WEDDING_REVIEW.md`.
- Time-based progression: `MONEY-011` — reward/time checkpoint crash consistency gap; `PROG-005` — short deserialized `Achievements` array can cause bounds exceptions; `PROG-006` — nullable `TimeInfo` can interrupt shared minute processing. Static only; DB-row prevalence and crash replay remain unverified; see `ONLINE_REWARDS_REVIEW.md`.
- Taxi meter path: `MONEY-012`/`PROG-007` — unverified client mileage can bill an active passenger and advance taxi mileage tasks. RAGE reproduction pending; see `TAXI_MILEAGE_REVIEW.md`. `VEH-011` separately records negative signed mileage wrapping the transient unsigned odometer counter.
- Passport progression: `PROG-008` — self-target request/accept can satisfy the active “show passport” task if RAGE entity argument resolves as expected; staging check pending; see `DOCUMENTS_REVIEW.md`.
- House transactions/tax: `MONEY-016..019` cover conditional sale/purchase/transfer settlement and tax persistence gaps; `PROP-003` covers conditional resurrection after tax repossession. `MONEY-003` records replayable bank-transfer confirmation state; `MONEY-004` records the policy-dependent ATM location/eligibility bypass; `MONEY-022` records business order state that may not be saved with its bank debit/refund and `MONEY-025..026` record order-count overflow credit and stale-BizID business-sale payout replay; `JOB-001` records delivery-order reservation before cargo validation, `JOB-004` records Trucker order consumption despite an unchecked wallet payout failure, and `JOB-002..003` phone taxi/mechanic dispatch takeover, stale timers and unthrottled repeat calls; `SEC-007..010`, `PHONE-001..006`, `MONEY-027..028` and `PROG-009` cover SMS CEF/remote-image sinks, Tinder/News CSS resource-loading candidates, phone queue/settings/SIM lifecycle risks, replayable Tinder match messages, cosmetic animation spoof, async News charge-without-ad risk and contact-task progress bypass; auction findings `MONEY-023..024`, `MONEY-038` and `PROP-004..005` cover first-bid failure, stale ended-bid handling, unchecked bid-fee overflow that can reverse a debit into a credit, and property award/listing persistence. Static-only; see the linked property/bank reviews.
- House furniture: `INV-009` — crafting counts recipe materials across all character sub-locations but removes only from inventory; direct slot-policy bypass may create furniture without consuming materials. See `HOUSE_FURNITURE_REVIEW.md`. Latest wider remote pass added `INV-010` (weapon ammo return quantity is used before clip cap), `INV-011` (Other-item auction escrow has no award/return path), and `PROG-010` (direct belt remote advances task 86 without a server-validated fasten action); both are static findings requiring RAGE staging, not runtime-confirmed. Phone group cross-check did not duplicate existing `PROG-009` / `PHONE-002..003` issues. The following showroom pass added `MONEY-029` for charge-before-color-validation failure in purchases/test drives. Latest generic Main remote review adds `MONEY-030` (conditional festive coin→RedBuck exchange without exact item consumption), `MONEY-031` (unauthorized government fuel-limit mutation); both require runtime checks and remediation. See `WEAPON_REMOTE_REVIEW.md`, `SELECTING_REMOTE_REVIEW.md`, `CARROOM_REVIEW.md` and `MAIN_REMOTE_REVIEW.md`.
- House resident ACL: `PROP-001` — roommate remotes can toggle self/other permissions or evict roommates because they use owner-or-roommate house lookup; `PROP-002` — resident writes are not marked dirty for the house persistence worker. Static-only; downstream impact/restart not tested. See `HOUSE_RESIDENT_REVIEW.md`.
- Organization fleet vehicle slice: `MONEY-014` records conditional payout-before-async-delete replay risk, `MONEY-015` records the ignored evacuation debit result when wallet change may fail during shutdown. Access checks traced but staging tests pending. See `ORG_VEHICLE_REVIEW.md`.
- Vehicle/garage: `VEH-001` is policy-dependent self-repair callback; `VEH-002` records missing household ownership validation in `server.garage.parking` (unauthorized association/recreation path, exact theft impact unproven); `VEH-003` records negative garage slot keys that can persist and fail spawn; `VEH-004..005` cover missing aircraft action/entity authorization (runtime reachability pending); `VEH-006`/`MONEY-013` cover stale sale confirmation and conditional payout/delete failure; `VEH-007..008` cover vehicle-sync entity authorization and passenger radio policy. Static-only, staging tests unavailable. See the linked vehicle review files.

- Fraction stock/cargo review: `STOCK-001` records non-atomic character↔fraction and vehicle↔fraction transfers; callers ignore `Remove`/`AddNewItem`/`Wallet.Change` outcomes and mutate stock without a verified exact transfer. Static only; fault-injection, replay, concurrency and restart tests remain pending. See `FRACTION_STOCK_REVIEW.md`.
- Business retail review: `STOCK-002` records takeProd stock decrement before owner-bank confirmation and retail callers ignoring customer debit/item-grant results; `MONEY-022` now also covers stock dirty-save omissions. Static only; see `BUSINESS_RETAIL_REVIEW.md`.

## Документы

- [ROADMAP](ROADMAP.md) — этапы, приоритеты, статусы и блокеры.
- [AUDIT_COVERAGE](AUDIT_COVERAGE.md) — матрица покрытия подсистем и критерии завершения полного аудита.
- [ARCHITECTURE](ARCHITECTURE.md) — компоненты и подтверждённая часть startup path.
- [DEPENDENCIES](DEPENDENCIES.md) — .NET/NuGet/npm версии, lockfiles и build setup.
- [EXTERNAL_INTEGRATIONS](EXTERNAL_INTEGRATIONS.md) — endpoint hostnames и проверка переноса интеграций.
- [SECURITY_REVIEW](SECURITY_REVIEW.md) — первоначальный auth/password/security анализ.
- [ECONOMY_REVIEW](ECONOMY_REVIEW.md) — статический review RedBucks, банковских переводов, ATM и фонового сохранения денег.
- [PAYMENTS_REVIEW](PAYMENTS_REVIEW.md) — обработка внешних receipts, DonatePack и надёжность выдачи платежных наград.
- [INVENTORY_REVIEW](INVENTORY_REVIEW.md) — remote inventory move/stack, tent ownership и отложенная запись предметов.
- [ROULETTE_REVIEW](ROULETTE_REVIEW.md) — remote case purchase/open count validation, wallet/item side effects и staging regression matrix.
- [CASINO_REVIEW](CASINO_REVIEW.md) — NewCasino Roulette bet/cancel/disconnect settlement audit and staging matrix.
- [BLACKJACK_REVIEW](BLACKJACK_REVIEW.md) — blackjack remote join, bet, move, payout and disconnect audit.
- [SPIN_REVIEW](SPIN_REVIEW.md) — slot join/bet/refund, payout math and computed RTP review.
- [HORSES_REVIEW](HORSES_REVIEW.md) — Inside Track betting, race reveal/refund, session and scheduler review.
- [LUCKYWHEEL_REVIEW](LUCKYWHEEL_REVIEW.md) — daily wheel eligibility, prize-grant consistency, claim/replay and prize odds.
- [DICE_REVIEW](DICE_REVIEW.md) — legacy `/dice` acceptance, wager settlement, self-target policy and tie reroll flow.
- [LOTTERY_REVIEW](LOTTERY_REVIEW.md) — legacy lottery ticket purchase, shop-session validation, persistence and payday payout.
- [BATTLEPASS_REVIEW](BATTLEPASS_REVIEW.md) — BattlePass reward claims, durable receipt lifecycle, grant failure and mission/replay test scenarios.
- [SAPPER_REVIEW](SAPPER_REVIEW.md) — RedBucks Sapper wager validation, client-controlled RNG/payout, and BattlePass progress validation.
- [QUESTS_REVIEW](QUESTS_REVIEW.md) — partial quest remote/objective validation, Granny item grant and progression bypass review.
- [WEDDING_REVIEW](WEDDING_REVIEW.md) — marriage invitation and divorce settlement failure-path review.
- [ONLINE_REWARDS_REVIEW](ONLINE_REWARDS_REVIEW.md) — time-based reward/checkpoint crash consistency and achievement-array bounds review.
- [TAXI_MILEAGE_REVIEW](TAXI_MILEAGE_REVIEW.md) — client mileage trust in Taxi fare billing and BattlePass progression.
- [DOCUMENTS_REVIEW](DOCUMENTS_REVIEW.md) — passport request/accept flow and self-target task progression.
- [VEHICLE_REPAIR_REVIEW](VEHICLE_REPAIR_REVIEW.md) — self-repair dialog callback, missing repair intent/location checks and staging matrix.
- [GARAGE_REVIEW](GARAGE_REVIEW.md) — house garage remote ownership validation, global vehicle-ID resolution and negative slot-index persistence review.
- [VEHICLE_ACTION_REVIEW](VEHICLE_ACTION_REVIEW.md) — vehicle action and tuning remotes, aircraft ownership checks, entity marshalling and staging tests.
- [VEHICLE_SALE_REVIEW](VEHICLE_SALE_REVIEW.md) — government sale confirmation ownership revalidation and conditional payout/delete crash consistency.
- [VEHICLE_SYNC_REVIEW](VEHICLE_SYNC_REVIEW.md) — vehicle dirt/indicator entity remotes and shared radio-station authorization/range review.
- [ORG_VEHICLE_REVIEW](ORG_VEHICLE_REVIEW.md) — organization fleet vehicle access, rank, evacuation and sale persistence review.
- [HOUSE_RESIDENT_REVIEW](HOUSE_RESIDENT_REVIEW.md) — roommate permission/eviction authorization and resident dirty-save persistence review.
- [HOUSE_FURNITURE_REVIEW](HOUSE_FURNITURE_REVIEW.md) — furniture craft ingredient slot mismatch, phone-house route and related property boundaries.
- [WEAPON_REMOTE_REVIEW](WEAPON_REMOTE_REVIEW.md) — weapon reload/remove/ammo-return remote boundaries and `INV-010`.
- [SELECTING_REMOTE_REVIEW](SELECTING_REMOTE_REVIEW.md) — Core player/object/vehicle interaction remotes, phone cross-check and `PROG-010`.
- [MAIN_REMOTE_REVIEW](MAIN_REMOTE_REVIEW.md) — generic `Main.cs` input/dialog callbacks, ticket settlement/replay, mayor treasury withdrawal, fuel controls, festive exchange, gang drug purchase arithmetic and waypoint progress remotes.
- [CARROOM_REVIEW](CARROOM_REVIEW.md) — car showroom purchase/test-drive validation, payment ordering and cleanup (`MONEY-029`).
- [PROPERTY_PURCHASE_REVIEW](PROPERTY_PURCHASE_REVIEW.md) — house purchase ownership/debit ordering and shutdown wallet-rejection review.
- [PROPERTY_SALE_REVIEW](PROPERTY_SALE_REVIEW.md) — house sale confirmation, owner persistence and payout crash-consistency review.
- [PROPERTY_TRANSFER_REVIEW](PROPERTY_TRANSFER_REVIEW.md) — player-to-player house offer, acceptance, wallet and owner settlement review.
- [PROPERTY_TAX_REVIEW](PROPERTY_TAX_REVIEW.md) — hourly house-tax account persistence, repossession owner dirty-save and restart behavior.
- [ATM_REVIEW](ATM_REVIEW.md) — ATM remotes, withdrawal location/eligibility and house-account access checks.
- [BANK_TRANSFER_REVIEW](BANK_TRANSFER_REVIEW.md) — bank transfer confirmation replay, one-shot state and cooldown enforcement.
- [BUSINESS_ORDER_REVIEW](BUSINESS_ORDER_REVIEW.md) — business phone purchase/cancel/price mutation, quantity-overflow bank-credit path and dirty-save persistence review.
- [BUSINESS_RETAIL_REVIEW](BUSINESS_RETAIL_REVIEW.md) — retail stock decrement, owner bank credit, customer debit and item/weapon grant settlement.
- [BUSINESS_BANK_REVIEW](BUSINESS_BANK_REVIEW.md) — ATM business-account deposit, unchecked second-leg credit and BizID/session validation.
- [BUSINESS_TAX_REVIEW](BUSINESS_TAX_REVIEW.md) — hourly business tax bank persistence and online/offline repossession compensation.
- [VEHICLE_PLAYER_SALE_REVIEW](VEHICLE_PLAYER_SALE_REVIEW.md) — player-to-player vehicle sale debit/credit and asynchronous holder persistence.
- [BUSINESS_SALE_REVIEW](BUSINESS_SALE_REVIEW.md) — generic phone sale callback, business/BizIDs persistence ordering and conditional payout replay.
- [BUSINESS_DELIVERY_REVIEW](BUSINESS_DELIVERY_REVIEW.md) — Trucker order reservation, cargo acquisition and cancellation/disconnect state review.
- [PHONE_MESSAGES_REVIEW](PHONE_MESSAGES_REVIEW.md) — contact-task progress, SMS CEF rendering/bridge sinks and message-history queue persistence review.
- [PHONE_CALL_TINDER_REVIEW](PHONE_CALL_TINDER_REVIEW.md) — call-state, sound-setting bounds, phone-info persistence, Tinder action replay and avatar CSS resource-loading review.
- [PHONE_NEWS_REVIEW](PHONE_NEWS_REVIEW.md) — phone News advert debit/persistence ordering, published image-link CSS path and Forbes visibility boundary review.
- [PHONE_SIM_REVIEW](PHONE_SIM_REVIEW.md) — SIM ownership/install/remove consistency, gallery/camera boundaries and phone animation remote review.
- [PHONE_DISPATCH_REVIEW](PHONE_DISPATCH_REVIEW.md) — taxi/mechanic dispatch claim and rate-limit remotes plus narrow cars/property/GPS/read-endpoint checks.
- [HOUSE_SALE_REVIEW](HOUSE_SALE_REVIEW.md) — player-to-player house sale settlement, unchecked buyer/seller wallet results, ownership ordering and incorrect seller UUID in money log (MONEY-037).
- [WALLET_REVIEW](MAIN_REMOTE_REVIEW.md#money-036--walletchange-truncates-long-character-balance-to-int) — shared long/int balance truncation affecting all Wallet.Change callers.
- [FRACTION_STOCK_REVIEW](MAIN_REMOTE_REVIEW.md#money-035--faction-cash-withdrawal-ignores-wallet-credit-result) — faction cash transfer and partial inventory-grant settlement findings MONEY-035/STOCK-001.
- [AUCTION_REVIEW](AUCTION_REVIEW.md) — auction first-bid settlement, expired-lot checks, property listing durability and offline business winner persistence.
- [FUTURE_FEATURES](FUTURE_FEATURES.md) — backlog solo-mode/NPC-симуляции; отложен до завершения аудита.
- [ISSUES](ISSUES.md) — нумерованный журнал рисков/вопросов.
- [TEST_PLAN](TEST_PLAN.md) — baseline и следующие тестовые наборы.
- [BUILD_LOG](BUILD_LOG.md) — команды/результаты сборок.
- [CHANGELOG](CHANGELOG.md) — история локальной подготовки и аудита.
- [SESSION_HANDOFF](SESSION_HANDOFF.md) — перенос текущего статуса RedAge в новый чат и ограничения PR/Git.
- [INITIAL_AUDIT](../INITIAL_AUDIT.md) — краткий исходный обзор.

- [BUSINESS_OWNERSHIP_REVIEW](BUSINESS_OWNERSHIP_REVIEW.md) — government business acquisition and player-to-player business transfer settlement (`MONEY-043..044`); buyer debit/seller credit and BizIDs/owner consistency.

- [BUSINESS_FUEL_REVIEW](BUSINESS_FUEL_REVIEW.md) — government fleet refuelling quota and consistency of fraction FuelLeft, City Hall funds, business stock and vehicle fuel (`MONEY-045`).

- [PETSHOP_REMOTE_REVIEW](PETSHOP_REMOTE_REVIEW.md) — pet-shop remote authorization, stale TempBizID, teleport ordering, replay and pet-model allowlist (`PET-001`).

- [TUNING_REMOTE_REVIEW](TUNING_REMOTE_REVIEW.md) — LS Customs tuning intent, organization exit state leak and personal tuning remote authorization (`VEH-010`).

- `BUSINESS_FUEL_REVIEW.md` also tracks `VEH-009`: petrol remote lacks active fuel-station/location context and can reuse a stale/non-fuel BizID.

- [MECHANIC_SERVICE_REVIEW](MECHANIC_SERVICE_REVIEW.md) — AutoMechanic repair/fuel offer settlement, two-sided wallet results, work-vehicle fuel reserve and replay/restart tests (`JOB-005`).

- `BUSINESS_OWNERSHIP_REVIEW.md` also covers admin deletion consistency (`BUG-002`) and owner refund settlement (`MONEY-047`).

- [VEHICLE_TRUNK_ACCESS_REVIEW](VEHICLE_TRUNK_ACCESS_REVIEW.md) — vehicle trunk inventory session binding and per-operation authorization (`INV-012`), with explicit open-trunk policy boundary.
