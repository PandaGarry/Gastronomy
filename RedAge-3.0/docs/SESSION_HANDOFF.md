# RedAge 3.0 — актуальная точка продолжения

**Срез:** 2026-11-08  
**Рабочая ветка:** `redage/audit-continuation`  
**Рабочий PR:** [#4 — Draft](https://github.com/PandaGarry/Gastronomy/pull/4)  
**Область изменений:** только `RedAge-3.0/`

> Это короткий handoff, а не исторический журнал. Старые подробности и evidence находятся в subsystem review и CHANGELOG.

## 1. Git safety

- Работать только в `redage/audit-continuation`; `main` напрямую не менять.
- Рабочая ветка основана на `arena/fab5bf55-gastronomy`, PR #4 нацелен на `main`.
- Сравнение refs: `diverged`, рабочая ветка behind by 1 commit и ahead by hundreds относительно `main`, merge base `aa07885aba2cc5a83f6cdcf35ff336b63c0fbc7a`. Mergeability может меняться между проверками; не менять PR base и не выполнять merge до отдельного ancestry/diff reconciliation и одобрения владельца.
- PR #4 остаётся Draft; не объявлять его готовым к merge.

## 2. Последние source changes

### MONEY-033 — ticket intent replay

В `dotnet/resources/NeptuneEvo/Fractions/FractionCommands.cs`:
- `ticketToTarget` записывает pending ticket под `lock(targetSessionData)` и не перезаписывает уже ожидающий штраф.
- `ticketConfirm` под тем же lock проверяет и отсоединяет pending intent, заменяя его новым `TicketsData` до settlement side effects.
- Повторный/конкурентный callback не должен повторно использовать тот же in-memory intent.
- Это не durable receipt и не атомарная выплата.

### MONEY-060 — payout after failed debit

- Если `Wallet.Change` и fallback `Bank.Change` оба возвращают `false`, handler уведомляет стороны и немедленно выходит.
- City Hall/officer split credits, success events и paid `GameLog.Ticket` после двух неуспешных debit не выполняются.

**Статус обоих:** source patch внесён и повторно прочитан; C# build, RAGE staging, MariaDB fault-injection, concurrency/restart tests не выполнялись.

## 3. Денежная архитектура — текущая реальность

- MONEY-002: есть частичная in-process coordination между `Wallet.Change`, detached money worker и full `Character.SaveSql`; revision/lock/retry hand-off guards внесены.
- Очередь остаётся process-memory и не переживает crash до flush.
- Direct SQL cash writers ещё обходят coordinator: offline AddMoney/refund/referral/business repossession/admin/merger и другие domain-specific paths требуют повторной inventory и миграции.
- Durable operation receipt/outbox, единый per-UUID transaction owner, login/cache publication gate, bounded retry/backoff/dead-letter и удаление legacy absolute writers ещё не реализованы.
- MONEY-003: банковский transfer синхронизирован в памяти, но две DB записи не являются одной durable transaction; bank ledger — отдельная область от character cash.
- DB API reconnaissance: `ServerBD` — linq2db `DataConnection` с `MySql.Data.MySqlClient`; linq2db 3.3.0 имеет sync `BeginTransaction(IsolationLevel)` и async `CommitAsync/RollbackAsync`. Legacy `MySQL` helper использует отдельный `MySqlConnector` path и не должен смешиваться с coordinator transaction.

Не объявлять MONEY-002 или MONEY-003 закрытыми.

## 4. Документы — источник статуса

1. [DOCS_STATUS.md](DOCS_STATUS.md) — правила, иерархия и единые статусы.
2. [REDAGE_MASTER_PLAN.md](REDAGE_MASTER_PLAN.md) — стратегия и Definition of Done.
3. [ISSUES.md](ISSUES.md) — текущие finding IDs и статусы.
4. [ECONOMY_REVIEW.md](ECONOMY_REVIEW.md), [MAIN_REMOTE_REVIEW.md](MAIN_REMOTE_REVIEW.md) — доказательства и оставшаяся remediation.
5. [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md) — незавершённые действия.
6. [TEST_PLAN.md](TEST_PLAN.md) и [BUILD_LOG.md](BUILD_LOG.md) — только реально выполненные/ожидающие проверки.
7. [AUDIT_COVERAGE.md](AUDIT_COVERAGE.md) — границы охвата.
8. [CHANGELOG.md](CHANGELOG.md) — история, не источник текущего статуса.

## 5. Следующие шаги

1. Повторно инвентаризировать все writers `characters.money` и все точки login/cache publication; составить полный список call sites с семантикой online/offline.
2. Runtime-проверить фактический `ServerBD` provider и InnoDB DDL в disposable MariaDB; API reconnaissance уже выполнен: linq2db 3.3.0 использует `BeginTransaction(IsolationLevel)` + `CommitAsync/RollbackAsync`.
3. Утвердить durable receipt schema, operation ID policy, conditional bounded delta, transaction ownership и typed outcomes.
4. Реализовать coordinator вместе с login/cache gate; только затем по одному мигрировать direct writers и success side effects.
5. Для каждого шага синхронно обновлять ISSUE, review, TEST_PLAN, checklist, master plan, roadmap, handoff и changelog.
6. Запустить build, DB failure/commit-ack tests, concurrency/replay/restart tests и RAGE staging, когда доступно соответствующее окружение.

**Ограничение:** статическая проверка не является сборкой или runtime validation. Ни один тест не отмечать пройденным без фактического запуска и записи результата в BUILD_LOG/TEST_PLAN.
