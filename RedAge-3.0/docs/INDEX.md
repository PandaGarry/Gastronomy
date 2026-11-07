# Документация RedAge 3.0

Обновлено: 2026-11-07. Источник: commit `23730b8cd464f86c47eaae6f80d182cd651092b2`; рабочая копия частичная. В `SOURCE_SNAPSHOT.md` указаны границы и локально очищенные конфиги.

## Текущий статус

- Аудит продолжается; кроме документации, в inventory move/stack внесены два узких local hardening changes (`INV-001..002`), но они пока не скомпилированы и не проверены в RAGE staging.
- Client JS bundle собран в изолированной копии.
- CEF build и C# build заблокированы текущими ограничениями toolchain/RAM.
- SQL import/RAGE smoke tests ожидают одноразовую test DB и полный runtime/assets.
- Найдены и локально очищены credential-bearing значения; если они были активны, владельцу нужно их ротировать.
- Auth review выявил legacy password hash без соли; миграция не выполнена, требуется отдельный backward-compatible план.
- Economy/payment review зарегистрировал RedBucks debit/credit, deferred persistence, transfer replay, ATM validation, external receipt idempotency, DonatePack intent risks и roulette negative-count/overflow credit path. Для roulette внесены только узкие input guards; все такие изменения ещё требуют build/staging tests.

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
- [FUTURE_FEATURES](FUTURE_FEATURES.md) — backlog solo-mode/NPC-симуляции; отложен до завершения аудита.
- [ISSUES](ISSUES.md) — нумерованный журнал рисков/вопросов.
- [TEST_PLAN](TEST_PLAN.md) — baseline и следующие тестовые наборы.
- [BUILD_LOG](BUILD_LOG.md) — команды/результаты сборок.
- [CHANGELOG](CHANGELOG.md) — история локальной подготовки и аудита.
- [SESSION_HANDOFF](SESSION_HANDOFF.md) — перенос текущего статуса RedAge в новый чат и ограничения PR/Git.
- [INITIAL_AUDIT](../INITIAL_AUDIT.md) — краткий исходный обзор.
