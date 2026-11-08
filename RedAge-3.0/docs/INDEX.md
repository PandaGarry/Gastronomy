# Документация RedAge 3.0

Обновлено: 2026-11-08. Рабочий статус ведётся в `DOCS_STATUS.md`; согласованная стратегия — `REDAGE_MASTER_PLAN.md`; актуальные findings — `ISSUES.md`. Исторические заметки ниже не переопределяют текущие статусы.

## Текущий статус — 2026-11-08

- Полный аудит RedAge 3.0 **не завершён**. Большинство findings — результаты статического анализа; RAGE:MP/DB воспроизведение и полный regression suite остаются обязательными.
- Рабочая ветка: `redage/audit-continuation`; Draft PR #4 направлен в `main`, но ветка основана на `arena/fab5bf55-gastronomy`. История расходится; merge запрещён до отдельного reconciliation.
- Денежная система: MONEY-002 — частичная in-process координация, не durable ledger; MONEY-003 — частичная защита bank transfer; MONEY-033 — consume-once ticket intent guard; MONEY-060 — early return при отказе обоих debit paths. Все остаются открытыми до необходимых DB/RAGE/build tests и durable settlement.
- Последний ticket patch повторно прочитан. C# build, MariaDB fault-injection, concurrency/restart и RAGE staging tests не запускались.
- C#/.NET и DB/RAGE staging проверки заблокированы доступностью соответствующих инструментов и runtime. Реальные результаты и ограничения см. в `BUILD_LOG.md`.
- Правила иерархии документации и единые статусы: [DOCS_STATUS](DOCS_STATUS.md). Согласованная стратегия: [REDAGE_MASTER_PLAN](REDAGE_MASTER_PLAN.md). Текущие findings: [ISSUES](ISSUES.md). Полнота покрытия: [AUDIT_COVERAGE](AUDIT_COVERAGE.md).

## Документы

- [DOCS_STATUS](DOCS_STATUS.md) — иерархия документов, единые статусы, цикл синхронизации и актуальные денежные блокеры.

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

- [VEHICLE_TRUNK_LIFECYCLE_REVIEW](VEHICLE_TRUNK_LIFECYCLE_REVIEW.md) — vehicle trunk reservation release on auxiliary-pane close/context replacement and stale-owner-safe cleanup (`VEH-012`).

- [AIRDROP_REMOTE_REVIEW](AIRDROP_REMOTE_REVIEW.md) — AirDrop hack state, client-supplied lock progress and loot-open authorization (INV-013).
- [MATWAR_REMOTE_REVIEW](MATWAR_REMOTE_REVIEW.md) — MatWar active-war/spatial authorization, client-supplied lock progress and stale loot cleanup (INV-014).

- [FRACTION_STOCK_SESSION_REVIEW](FRACTION_STOCK_SESSION_REVIEW.md) — stale OnFracStock authorization and faction weapon-stock remote access (INV-015).

- [ORGANIZATION_STOCK_SESSION_REVIEW](ORGANIZATION_STOCK_SESSION_REVIEW.md) — organization stock context remains mutable after leaving the organization interior (INV-016).

- [FURNITURE_SAFE_SESSION_REVIEW](FURNITURE_SAFE_SESSION_REVIEW.md) — furniture safe inventory context remains mutable after house exit (`INV-017`).

- [HELICRASH_KEYCLAMP_REVIEW](HELICRASH_KEYCLAMP_REVIEW.md) — HeliCrash lockpick/minigame bypass through client-controlled keyClamp.end (`INV-018`).

- [WEAPON_KEYRING_SUBCONTAINER_REVIEW](WEAPON_KEYRING_SUBCONTAINER_REVIEW.md) — parent-item ownership binding for weapon attachments and CarKey subcontainers (`INV-019`); static finding, staging required.

- [BANK_TRANSFER_REVIEW](BANK_TRANSFER_REVIEW.md) — ATM confirmation replay (`MONEY-003`), non-durable two-account transfer persistence (`MONEY-058`) and signed SQL INT balance boundary (`MONEY-059`).

- Ticket settlement: MONEY-033 consume-once intent guard and MONEY-060 early return after both debit failures are patched; durable receipt/split payout and runtime tests remain open. See `MAIN_REMOTE_REVIEW.md`, `ECONOMY_REVIEW.md` and `TEST_PLAN.md`.
