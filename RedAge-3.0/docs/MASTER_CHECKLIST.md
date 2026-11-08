# RedAge 3.0 — Master Checklist

Обновлено: 2026-11-08
Рабочая ветка: `redage/audit-continuation`
База рабочей ветки: `arena/fab5bf55-gastronomy`
Целевая ветка релиза: `main` (не изменять напрямую).

> **Главный план проекта:** [`REDAGE_MASTER_PLAN.md`](REDAGE_MASTER_PLAN.md) — единый источник истины по согласованным целям, этапам аудита, тестированию, оптимизации, блокерам и Definition of Done. Этот файл остаётся оперативным чек-листом конкретных задач; при расхождении общую стратегию сверять с мастер-планом.


## Правила безопасной работы

- [ ] Перед каждым изменением проверить актуальные refs, diff и полный data flow.
- [ ] Все изменения RedAge держать только внутри `RedAge-3.0/`; не менять корневые файлы Gastronomy.
- [ ] Не отправлять изменения в upstream `ragemp-pro/redage_v3`.
- [ ] Каждый finding получает ID, severity, точные code references, confidence, remediation и regression tests.
- [ ] Не считать статический finding runtime-подтверждённым.
- [ ] Не закрывать finding до C# build и релевантных RAGE:MP/MySQL regression tests.
- [ ] Денежные операции проектировать атомарно и идемпотентно; не доверять клиентскому результату.
- [ ] Не использовать production DB, реальные платёжные данные или реальные credentials для тестов.
- [ ] Каждый патч сопровождается обновлением ISSUES, соответствующего review, TEST_PLAN, BUILD_LOG, CHANGELOG, ROADMAP и AUDIT_COVERAGE по применимости.
- [ ] Перед merge проверять PR diff, тесты, конфликты и возможность rollback.

## Этап A — Репозиторий и контроль изменений

- [x] GitHub read access подтверждён.
- [x] GitHub write access проверен реальной операцией создания ветки.
- [x] Создана рабочая ветка `redage/audit-continuation` от `arena/fab5bf55-gastronomy`.
- [ ] Сверить уникальные коммиты `main` и `arena/fab5bf55-gastronomy`; не объединять ветки вслепую.
- [ ] Подтвердить лицензионные права на исходники, UI и игровые ассеты.
- [ ] Проверить видимость репозитория и секреты; ротировать любые действовавшие credentials, если это требуется.
- [ ] Согласовать базу и target для первого Draft PR.

## Этап B — Воспроизводимая сборка и стенд

- [ ] Закрепить совместимую версию .NET SDK/runtime для `netcoreapp3.1` и RAGE:MP.
- [ ] Закрепить NuGet/npm зависимости и создать проверенные lockfiles.
- [ ] Повторить C# build на изолированном агенте.
- [ ] Завершить CEF production build на агенте с достаточной RAM.
- [ ] Поднять одноразовую MySQL test DB и проверить импорт/restore.
- [ ] Поднять RAGE:MP staging с тестовыми аккаунтами.
- [ ] Подготовить fault-injection, replay, concurrency и restart test harness.

## Этап C — Критичные деньги, платежи и игровые активы

- [ ] MONEY-008/009, PROG-001 — Sapper: серверная state machine, RNG, ход, cashout, exactly-once settlement.
- [ ] STOCK-001 — faction/organization/vehicle stock and cargo transfers: exact Remove/AddNewItem/Wallet.Change result, atomicity, authorization, idempotency and restart recovery; include partial grants and all stock containers. See `FRACTION_STOCK_REVIEW.md` and `ISSUES.md`.
- [ ] MONEY-042 — player-to-player vehicle sale: check buyer debit and seller credit, durable holder DB commit, sale receipt/idempotency and rollback/reconciliation across restart. See VEHICLE_PLAYER_SALE_REVIEW.md.
- [ ] MONEY-040/041 — business hourly tax and repossession: mark ordinary tax debit dirty/persistent; durable idempotent online/offline owner compensation before business ownership release. See BUSINESS_TAX_REVIEW.md.
- [ ] MONEY-039 — ATM business-account deposit: atomic player debit/business credit, result checking, stale BizID/index validation, retry/refund and replay protection. See BUSINESS_BANK_REVIEW.md.
- [ ] STOCK-002 — business retail stock and customer settlement: takeProd rollback, owner-bank credit, customer Wallet.Change, exact item/weapon grant, missing product rejection, dirty-save and exactly-once behavior. See BUSINESS_RETAIL_REVIEW.md.
- [ ] MONEY-030 — EventCoins: точное списание из разрешённого контейнера до начисления RB.
- [ ] MONEY-031 — Fuel Control: server-side role/fraction authorization и input bounds.
- [ ] MONEY-032 — Mayor treasury withdrawal: confirm bank credit before treasury debit; transactional/restart-safe settlement.
- [ ] MONEY-033 — Ticket settlement: successful debit required, server-side one-shot intent and durable idempotent payout.
- [ ] MONEY-034 — Gang drug purchase: quantity cap, checked/long cost+capacity math, exact item-grant result before faction debit.
- [ ] MONEY-035 — Faction/organization money withdrawal: check wallet credit result; atomic stock/player balance transfer.
- [ ] MONEY-037 — Player-to-player house sale: buyer debit and seller credit must both succeed before ownership transfer; correct seller UUID in money log; idempotent offer settlement and crash/replay tests; see `HOUSE_SALE_REVIEW.md`.
- [ ] MONEY-038 — source patch on branch: reject nonpositive bids and widen fee arithmetic to `long`; pending C# build, RAGE boundary/failure tests and owner decision on maximum bid; see `AUCTION_REVIEW.md`.
- [ ] MONEY-036 — resolve wallet width contract: `CharacterData.Money` is long but DB `characters.money` is int(11); choose explicit Int32 cap or end-to-end BIGINT migration, then test checked arithmetic and persistence round-trip.
- [ ] Review organization stock implementation against the same money/item settlement invariants.
- [ ] MONEY-022/025/026 — business order dirty-save, unchecked cancel-refund result, quantity overflow, government-sale unchecked payout/ownership release and stale-BizID replay; include `JOB-004` Trucker payout settlement.
- [ ] MONEY-003/004 — bank transfer replay и ATM policy/location.
- [ ] MONEY-005, PAY-001..003 — payment receipts, durable idempotency и compensation.
- [ ] MONEY-001/002/011/012 — money queue, online reward checkpoint, taxi mileage/fare.
- [ ] MONEY-013..019, 022, 023..024, 027..029 — property, vehicle, business and phone settlement/persistence; auction first-bid/null lookup and stale-end guards patched, runtime settlement tests pending.
- [ ] INV-001..011 — inventory/container ownership, counts, ammo, crafting and item lifecycle; include Other-item auction escrow award/return (`INV-011`, `AUCTION_REVIEW.md`).
- [ ] CAS-001..028 — casino state machines, RNG, wager limits, disconnect settlement and prize grants.
- [ ] PROP-001..005, VEH-001..008 — ownership/ACL, persistence, vehicle actions and recovery.

## Этап D — Auth, remotes и инфраструктура

- [ ] Versioned password-KDF migration with backward-compatible legacy verification.
- [ ] Review all 498 RemoteEvent mentions, 116 ServerEvent mentions and 382 Command mentions; inventory counts are not completion evidence.
- [x] Enumerate 38 `Main.ClientEvent_inputCallback` case occurrences (32 unique callback names); selected delegated helpers checked, remaining paths explicitly listed in `MAIN_REMOTE_REVIEW.md`.
- [ ] Finish every delegated `inputCallback` handler review, including stock, house/drug sale, street race, vehicle trade, hotel, tent and pet flows.
- [ ] Server-side ownership, permission, type/range, distance/dimension, rate-limit and replay checks.
- [ ] Audit shared collections, worker threads, lock ordering and RAGE thread affinity.
- [ ] DB TLS, least-privilege accounts, parameterized SQL, safe logs, timeout/retry/transaction behavior.
- [ ] External integration signatures, nonce/timestamp, idempotency, timeout/retry and secret rotation.

## Этап E — Качество, производительность и релиз

- [ ] Automated static checks and CI.
- [ ] C# unit/integration and RAGE staging regression suite.
- [ ] PERF-002 — run all three CEF production build scripts from clean shells; verify production mode, no source maps, hot reload disabled, output paths and RAGE:MP UI smoke tests. See `CEF_BUILD_REVIEW.md`.
- [ ] Profile CPU, RAM, tick latency and DB queries before optimization.
- [ ] Review CEF bridge, HTML/resource loading, accessibility and UX.
- [ ] Release checklist, backup/restore, rollback and incident drills.
- [ ] Consider solo-mode/NPC simulation only after security baseline and API/capacity validation.

## Definition of Done для каждого finding

- [ ] Reproducible source path and affected invariant documented.
- [ ] Fix reviewed for races, retries, exceptions, partial DB failures and disconnect/restart.
- [ ] Regression tests cover valid, invalid, boundary, duplicate/replay and concurrent inputs.
- [ ] Build and relevant staging tests pass; logs/results recorded.
- [ ] Docs, issue status and changelog updated.
- [ ] PR reviewed; merge only after owner approval.

## Текущие подтверждённые ограничения

- C# build, full CEF production build, disposable MySQL DB and RAGE:MP runtime are not yet available in this work context.
- MONEY-030/031 and Sapper issues are statically confirmed; no live exploitation or runtime test is claimed.
- `main` and `arena/fab5bf55-gastronomy` diverge by one unique commit on each side. Preserve both histories until the diff is reconciled.
- GitHub repository API currently reports visibility as public; verify and change in GitHub settings only if that is not intended.

- [ ] MONEY-043 — government business purchase: verify successful buyer debit before stock/order reset and owner/BizIDs mutation; durable receipt, rollback and restart tests. See `BUSINESS_OWNERSHIP_REVIEW.md`.
- [ ] MONEY-044 — player-to-player business transfer: atomic buyer debit + seller credit + owner/BizIDs commit; one-shot offer, idempotency, partial-write compensation and replay/concurrency tests. See `BUSINESS_OWNERSHIP_REVIEW.md`.

- [ ] MONEY-045 — government refuelling quota: validate currency-based FuelLeft against checked total cost before any stock, city-fund or vehicle-fuel mutation; test exhausted/partial quota, quantity clamp, replay and restart. See BUSINESS_FUEL_REVIEW.md.

- [ ] VEH-009 — bind petrol remote to active nearby Type==1 fuel station and current vehicle; stale BizID/non-fuel business must not authorize refuelling. Test direct remote, move-away, dimension swap, replay and legitimate station use. See BUSINESS_FUEL_REVIEW.md.

- [ ] JOB-005 — AutoMechanic repair/fuel service: confirm buyer debit and mechanic credit before repair/fuel transfer; durable one-shot offer, retry/compensation, buyFuel debit-before-reserve and replay/restart tests. See MECHANIC_SERVICE_REVIEW.md.

- [ ] BUG-002 — admin business deletion: handle null/offline owner before DB delete and keep DB row, BizIDs, runtime cache/world and restart state consistent. See BUSINESS_OWNERSHIP_REVIEW.md.
- [ ] MONEY-047 — admin business deletion refund: verify online owner compensation or persist retryable refund receipt before final delete. See BUSINESS_OWNERSHIP_REVIEW.md.

- [ ] PET-001 — pet-shop remote: require Type==14 active one-shot session, proximity/dimension and allowed pet enum; prevent stale TempBizID teleport/replay and validate wallet/stock settlement. See PETSHOP_REMOTE_REVIEW.md.

- [ ] VEH-010 — LS Customs tuning: clear organization tuning state on every exit; require active one-shot Type==12 intent, vehicle identity and location for personal purchase remote; test stale TuningShop and disconnect position resolution. See TUNING_REMOTE_REVIEW.md.

- [ ] VEH-011 — mileage remote: reject negative/oversized client deltas before uint conversion; bind accepted distance to server-measured movement/time and prevent counter wrap. Test int boundaries, replay/cadence and no fare/progression on invalid deltas. See TAXI_MILEAGE_REVIEW.md.

- [ ] INV-012 — vehicle trunk inventory: bind session to exact vehicle and authorized access policy; revalidate distance/dimension/door/ownership/rank on every move, stack, use and drop. Revoke stale sessions and test walk-away/replay. See VEHICLE_TRUNK_ACCESS_REVIEW.md.

- [ ] VEH-012 — release vehicle BagInUse reservation and clear SelectedVeh on auxiliary-pane close/context replacement, full close, disconnect and vehicle deletion; use an owner/session-bound idempotent release and test stale-owner races. See VEHICLE_TRUNK_LIFECYCLE_REVIEW.md.

- [ ] INV-013 — bind AirDrop hack/progress/open to a server-owned player+DropId+event-generation intent; require active event, exact crate, dimension/proximity and server-timed progress; reject client health/replay/cross-event calls. See AIRDROP_REMOTE_REVIEW.md.
- [ ] INV-014 — bind MatWar hack/progress/open to active war generation, exact player/ShapeId and nearby crate; server-authoritative progress; revoke and remove matwar_100 inventory on endWar. See MATWAR_REMOTE_REVIEW.md.

- [ ] INV-015 — replace stale OnFracStock with a short-lived faction-stock intent; revalidate rank, duty, IsOpenGunStock, location/dimension on open and every mutation; revoke on close/context change/disconnect. See FRACTION_STOCK_SESSION_REVIEW.md.

- [ ] INV-016 — revoke Organization inventory intent on RemovePlayer/interior exit; bind every mutation to current organization membership, stock-open state and dimension; test stale remotes and concurrent exit. See ORGANIZATION_STOCK_SESSION_REVIEW.md.

- [ ] INV-017 — revoke furniture safe context on house exit/object removal/ACL change; bind every item operation to exact house/object/access mode and current range/dimension. See FURNITURE_SAFE_SESSION_REVIEW.md.

- [ ] Remaining bounded container questions: warehouse location/quest policy and HeliCrash open/range lifecycle require owner-policy/staging confirmation; do not infer cross-player theft from personal UUID storage.
- [x] Static parent-item subcontainer trace completed; finding INV-019 registered. Runtime ownership-transfer/replay tests remain pending.

- [ ] INV-018 — make KeyClamp completion server-authoritative; require active player/box reservation and successful keyDown, validate progress/time, consume ArmyLockpick exactly once, clear state on all terminal paths. See HELICRASH_KEYCLAMP_REVIEW.md.

- [ ] INV-019 — bind `weapon_<SqlId>` / `CarKey_<SqlId>` subcontainer sessions to exact parent item and current owner; revalidate on every move/stack/use and revoke on transfer/drop/delete/replacement. See WEAPON_KEYRING_SUBCONTAINER_REVIEW.md.

- [ ] MONEY-051 — street race: require both stake debits to succeed before race start; test first/second debit failure, compensation failure, duplicate/concurrent accept/finish and payout receipt. See `STREET_RACE_REVIEW.md`.
- [ ] MONEY-052 — street race finish remote: require active race and server-side finish radius; validate finite/min-distance waypoint inputs, map bounds, replay/concurrency and payout recovery. See `STREET_RACE_REVIEW.md`.
- [ ] MONEY-050 — driving school: require successful wallet debit before granting any of six licenses or applying quest/faction/log/success side effects; validate all six failure paths and shutdown race. See `DRIVING_SCHOOL_REVIEW.md`.
- [ ] MONEY-049 — Metro ticket: checked `long` price calculation and require successful wallet debit before logging/success/dimension transition; test negative/zero/overflow inputs and wallet rejection. See `METRO_REVIEW.md`.
- [ ] MONEY-048 — player cash/item trade and tent-market purchase: checked bounded price; exact item and wallet settlement; durable one-shot receipt/compensation; verify both debit and credit before item movement, BattlePass progress or success; test shutdown/failure/overflow/replay/concurrency/restart. See `PLAYER_TRADE_REVIEW.md`.
\n\n- [ ] MONEY-003 — bank transfer: one-shot ATM confirmation; source ownership revalidation; synchronized two-account mutation; positive amount and checked arithmetic; revision-aware retryable persistence. Keep open until build, DB fault-injection, concurrency and RAGE replay tests pass. See BANK_TRANSFER_REVIEW.md.
- [ ] MONEY-002 — проверить частичный patch очереди денег: C# build; concurrent producers/snapshot; partial DB failure/retry; newer-value-wins; disconnect/reconnect; crash/restart loss. После этого спроектировать durable outbox, retry backoff и dead-letter. См. `ECONOMY_REVIEW.md`.\n
- [ ] BANK-SAVE — verify revision-aware save retry under DB outage, concurrent mutations and INT range boundaries; durable ledger/outbox still required for crash consistency. See BANK_TRANSFER_REVIEW.md.

- [ ] MONEY-003 follow-up — test atomic in-memory bank transfer, one-shot ATM confirmation, synchronized balance reads, checked account creation bounds, DB save retry/revision behavior, and restart recovery limitation. Audit mutable `Bank.Data` references. See `BANK_TRANSFER_REVIEW.md`.


- [ ] MONEY-003 follow-up — audit and remove every direct mutable bank balance write; property acquisition/tax/auction settlement must use synchronized bank APIs. Validate buyer debit/ownership ordering and DB failure compensation. See `BANK_TRANSFER_REVIEW.md`.
