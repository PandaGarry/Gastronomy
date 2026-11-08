# Статус и правила синхронизации документации RedAge 3.0

**Срез:** 2026-11-08  
**Рабочая ветка:** `redage/audit-continuation`  
**Рабочий PR:** [#4 — Draft](https://github.com/PandaGarry/Gastronomy/pull/4)  
**Область:** только `RedAge-3.0/`

> Этот файл устраняет разночтения между длинными историческими заметками. Он не заменяет доказательства в review-файлах и не закрывает findings.

## 1. Иерархия документов

| Документ | Единственная ответственность |
|---|---|
| `REDAGE_MASTER_PLAN.md` | Согласованная стратегия, этапы, принципы, Definition of Done и архитектурные решения |
| `ISSUES.md` | Реестр уникальных finding ID, приоритет, фактический статус и следующий шаг |
| `*_REVIEW.md` | Источник доказательств: точный source flow, предпосылки, ограничения и remediation |
| `MASTER_CHECKLIST.md` | Операционные задачи, которые ещё нужно выполнить |
| `TEST_PLAN.md` | Конкретные regression/failure/concurrency/restart сценарии и статус их выполнения |
| `BUILD_LOG.md` | Только реально выполненные команды сборки/проверок, версии инструментов и результаты |
| `CHANGELOG.md` | Хронология source/documentation изменений; не является реестром текущего статуса |
| `ROADMAP.md` | Очерёдность крупных этапов и блокеры |
| `SESSION_HANDOFF.md` | Краткая актуальная точка продолжения; старые записи явно помечаются как исторические |
| `AUDIT_COVERAGE.md` | Что просмотрено, что частично просмотрено и что ещё не начиналось |
| `INDEX.md` | Навигация и короткий актуальный обзор |

При конфликте статусов приоритет: **ISSUES.md → текущий subsystem review → TEST_PLAN.md/BUILD_LOG.md → MASTER_CHECKLIST.md → ROADMAP.md/INDEX.md/SESSION_HANDOFF.md**. Хронологические записи в CHANGELOG и старых handoff-разделах не переопределяют текущий статус.

## 2. Обязательный цикл обновления

Каждая source-задача выполняется одним связанным пакетом:

1. Повторно прочитать текущую ветку и полный source flow.
2. Зафиксировать/уточнить finding и acceptance criteria.
3. Внести минимальный безопасный патч либо документировать, почему патч без архитектурного решения опасен.
4. Обновить соответствующий review и строку в `ISSUES.md`.
5. Обновить/добавить тесты в `TEST_PLAN.md`.
6. Синхронизировать `MASTER_CHECKLIST.md`, `REDAGE_MASTER_PLAN.md`, `ROADMAP.md` и `SESSION_HANDOFF.md` по применимости.
7. Добавить запись в `CHANGELOG.md`; `BUILD_LOG.md` обновлять только при фактическом запуске команды.
8. Повторно сверить все упоминания finding ID и проверить ссылки/статусы в изменённых документах.

Не писать один и тот же длинный finding в нескольких местах: в кратких документах использовать ID и ссылку на review.

## 3. Единые статусы

Использовать только следующие формулировки:

- **Открыто — static finding:** дефект подтверждён чтением исходников; runtime не воспроизведён.
- **Патч внесён — static review passed; tests pending:** код изменён и повторно прочитан; сборка/runtime-тесты не выполнены.
- **Build passed; staging pending:** сборка реально прошла, но RAGE/DB проверки ещё нет.
- **Staging verified:** конкретные тесты реально прошли; указать окружение и артефакт/лог.
- **Закрыто:** выполнен Definition of Done, включая релевантные сборки, тесты, recovery/replay проверки и документацию.
- **Policy/owner decision required:** дальнейший код зависит от неутверждённого игрового правила.

Слова «исправлено», «готово» и «закрыто» не использовать как синоним факта коммита. Частичный guard не закрывает весь finding.

## 4. Текущий срез денежной системы

| ID | Фактическое состояние | Что остаётся |
|---|---|---|
| MONEY-002 | Частичная in-process координация Wallet / worker / full character save; retry hand-off защищён статически | Durable operation receipt/outbox, login publication gate, миграция всех прямых cash writers, retry/backoff/dead-letter, build/DB/concurrency/crash tests |
| MONEY-003 | Частичная защита ATM confirmation и синхронизация in-memory transfer/save | Одна DB transaction + stable transfer receipt, replay/concurrency/crash recovery, mutable bank-data audit |
| MONEY-033 | Добавлено consume-once ticket intent: pending state атомарно снимается под session lock до settlement | Durable receipt и атомарность debit + City Hall + officer legs; replay/concurrency/failure tests |
| MONEY-060 | Добавлен early return, если Wallet и Bank debit оба отказали | Durable one-shot fine settlement, успешные/частичные payout legs, build/RAGE/DB tests |

Для MONEY-002 не объявлять durable coordinator реализованным: текущая очередь остаётся process-memory, а прямые SQL cash writers ещё существуют. Банковский ledger (`money.balance`) — отдельная область и не считается автоматически покрытой character-cash coordinator.

## 5. Git и тестовая дисциплина

- Все изменения этой работы — только в `RedAge-3.0/` на `redage/audit-continuation`.
- `main` не менять напрямую; PR #4 остаётся Draft и не сливается автоматически.
- Рабочая ветка происходит от `arena/fab5bf55-gastronomy`; PR #4 нацелен на `main`. GitHub compare на текущем срезе: `diverged`, рабочая ветка behind by 1 commit и ahead by hundreds относительно `main`; merge base `aa07885aba2cc5a83f6cdcf35ff336b63c0fbc7a`. PR API сейчас сообщает `mergeable=true`, но merge запрещён до отдельного ancestry/diff reconciliation и одобрения владельца. До merge требуется отдельное reconciliation и review полного diff.
- Пустой GitHub CI status не означает успешный build.
- Static assertions не являются C# build, MariaDB transaction test или RAGE:MP runtime test.
- Не запускать destructive/fault-injection тесты на production и не использовать реальные платёжные данные.

## 6. Контрольный приоритет

Первый крупный поток — безопасная денежная архитектура: схема/engine verification → durable receipt contract → coordinator + transaction ownership → login/cache handoff → отключение legacy absolute writers → миграция доменных callers → fault-injection/concurrency/restart tests. До этого отдельные guards считаются ограниченными mitigations, а не завершением экономики.
