# Предварительный security review

Дата: 2026-11-07. Это статический обзор выбранных конфигов и auth/data-flow, не полноценный penetration test. Живые серверы/внешние endpoints не вызывались.

## Уже смягчено локально

- В рабочей копии очищены найденные DB credential-bearing values из `settings/mainDB.json` и закомментированной website DB строки в `Main.cs`; upstream не изменялся. Владелец должен ротировать их, если они когда-либо были действующими.
- В локальном `mainDB.json` сохранена только структура с заглушками, файл перечислен в upstream `.gitignore`.

## Authentication — подтверждённая проблема

### Текущий путь

1. CEF/client вызывает remote event входа `TryAutorize` с login/email и паролем.
2. Сервер вызывает `Accounts.Repository.GetSha256(password)`, затем передаёт хэш в `AutorizationAccount`.
3. Регистрация создаёт `AccountData.Password` тем же `GetSha256(pass_)`.
4. `GetSha256` преобразует пароль через `Encoding.ASCII.GetBytes` и вычисляет один быстрый SHA-256 без уникальной соли/стоимости.
5. Авторизация сравнивает полученное значение с `Accounts.Password` через ORM query.

### Риск

- Быстрый unsalted SHA-256 не предназначен для хранения паролей: при утечке БД массовый offline brute-force намного дешевле, чем с password KDF.
- ASCII-кодирование некорректно для международных символов: разные Unicode inputs могут свестись к одинаковым fallback bytes.
- Само обновление алгоритма может заблокировать старые аккаунты, поэтому не менять хэш-функцию прямо в `GetSha256` без миграционного плана.

### Безопасный план исправления (пока не реализован)

1. Добавить версионированный формат хэша и сильный salted password KDF (предпочтительно Argon2id; альтернативы выбирать по совместимости .NET/RAGE runtime).
2. При успешном входе проверять legacy SHA-256, затем в той же контролируемой операции сохранить новый KDF hash; для неактивных аккаунтов предусмотреть безопасный reset.
3. Не писать пароль/хэш в debug/error logs; использовать generic auth responses, rate-limit по аккаунту/IP/session и защиту от параллельных попыток.
4. Добавить unit tests: legacy verification, unicode inputs, bad password, concurrent attempts, upgrade after successful login, reset flow.
5. Провести backup/test DB миграцию и rollback rehearsal до production.

## Другие первичные зоны проверки

- В просмотренном `TryAutorize` явный per-account/IP cooldown не виден; `Queue` ограничивает часть in-flight login flow, но не является подтверждённым rate limiter.
- `Players.Queue.Repository` хранит игроков в обычных `List<ExtPlayer>` без `lock`/concurrent collection, а `QueueWorker` работает на отдельном `Thread`; remote handlers также вызывают `AddQueue`. Это подтверждённая многопоточная зона риска: возможны races при contains/add/remove/enumeration. Нужны отдельные concurrency tests и безопасная синхронизация.
- В `Register` видны проверки `session`/аккаунта и только непустых login/password/email в проверенном repository path; максимальные длины, Unicode normalization, email rules и rate-limit нужно проследить по всем вызываемым слоям.
- Login/registration remote handlers принимают строки от клиента; добавление строгих server-side length/format limits нужно проверить на совместимость с текущими клиентами и SQL column sizes.
- C# обнаружено 498 `[RemoteEvent]` атрибутов в 137 файлах. Обязательная следующая выборка: авторизация, регистрация/recovery, bank/money, inventory, donations, admin/fraction actions. Проверять server-side ownership, permission, bounds, rate limits, replay/duplicate calls и transaction semantics.
- `MySQL.Query` debug/error paths могут включать полный SQL text; подключение к БД настроено без TLS. См. `ISSUES.md`.
- Внешние payment/API/cloud/radio/CDN hostnames и call-site inventory перечислены в `EXTERNAL_INTEGRATIONS.md`; до staging не отправлять туда тестовые/пользовательские данные.
- Узкий phone pass: `SEC-007` records client-supplied SMS text interpolated into `mp.gui.emmit` and used with Svelte `{@html}`; direct remote bypasses the UI encoder. `SEC-008`/`SEC-009` are separate Tinder-avatar and moderator-approved News-link CSS/resource-loading candidates, and `SEC-010` is a recipient-side SMS image URL request path; these are not script-execution findings. They need compiled CEF/CSP/network staging; see `PHONE_MESSAGES_REVIEW.md`, `PHONE_CALL_TINDER_REVIEW.md` and `PHONE_NEWS_REVIEW.md`.

## Не делать сейчас

- Не менять password hashing in-place, не сбрасывать всех аккаунтов и не запускать SQL на чужой базе.
- Не включать payment callbacks/owner-specific API до проверки получателя, signature/nonce validation, idempotency и тестовых credentials.
- Не считать этот обзор заменой ручному коду и staging security test.
