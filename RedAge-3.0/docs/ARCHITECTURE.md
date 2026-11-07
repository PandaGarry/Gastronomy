# Карта архитектуры (предварительная)

## Компоненты

1. **RAGE:MP server/runtime** — внешний исполняемый сервер, `conf.json` настраивает базовые параметры. В локальном source snapshot бинарники/runtime исключены.
2. **C# gamemode** — `dotnet/resources/NeptuneEvo`; `.csproj` таргетирует `netcoreapp3.1`. Подсистемы верхнего уровня включают Accounts, Character, Businesses, Fractions, Houses, Inventory, Jobs, MoneySystem, Organizations, Players, Properties, Quests, VehicleData/VehicleModel, Voice и World.
3. **Shared C# libraries** — `NeptuneEvoSDK` и `Localization` в решении `NeptuneEvo.sln`.
4. **Client JS** — `src_client`; отдельный webpack build. Тестовая сборка прошла в ephemeral copy на Node 22 при включённом `--openssl-legacy-provider`.
5. **CEF UI** — `src_cef`; Svelte 3 + webpack, русская/английская и test конфигурации. Чистая установка обнаруживает webpack/cache-loader peer conflict; полный production build требует больше RAM, чем доступно в этой среде.
6. **Database** — `database/main.sql`, `mainconfig.sql`, `mainlogs.sql`; локальный `settings/mainDB.json` игнорируется Git, значения в рабочей копии — заглушки.
7. **Данные/настройки** — `json/`, `settings/`, `dotnet/vehicleData.json` и `dotnet/settings.xml`.

## Подтверждённая часть потока запуска

- `dotnet/resources/NeptuneEvo/meta.xml` объявляет RAGE:MP script resource `NeptuneEvo` и указывает собранную DLL под `bin/Debug/netcoreapp3.1/NeptuneEvo.dll`; путь/конфигурация Release требуют проверки.
- `NeptuneEvo.Main` — C# `Script`; constructor настраивает сущности и серверные параметры, вызывает `MySQL.Init()`, затем настраивает linQ2DB connection settings и запускает набор модулей (Redis, timers, economy, jobs/businesses/vehicles и др.).
- `Main` также имеет `[ServerEvent(Event.ResourceStart)]` handler для ресурсной инициализации. Порядок между constructor, RAGE resource lifecycle и асинхронными/таймерными задачами надо подтвердить на runtime.
- `MySQL.Init()` читает `mainDB` из локального Settings и формирует connection strings с `SslMode=None`; текущие `ConnectionInfo` также формируют `SSLMode=none`. Это требует отдельной проверки сетевого периметра и поддержки TLS на production DB.
- В `Main` вызывается `SET GLOBAL max_connections = 500` до конфигурации DataConnection; приложению может потребоваться глобальная привилегия, а значение должно управляться DBA/infra, не игровым кодом.
- `MySQL.Query` может записывать полный SQL text в debug/error log; проверяем, не попадают ли туда параметры пользователей/секреты.

Рабочий запуск пока нельзя считать подтверждённым: отсутствуют RAGE:MP runtime, точная версия server bootstrapper и полный пакет client assets. Перед инструкцией нужно изучить `run.sh`/официальный порядок запуска и протестировать на изолированном staging.

## Зависимости и внешние сервисы

- Версии .NET/NuGet/npm собраны в `DEPENDENCIES.md`; lockfiles и CI нет.
- В исходниках найдены owner-specific внешние API/CDN/payment/radio hostnames; подробности и безопасный план проверки в `EXTERNAL_INTEGRATIONS.md`. Внешние запросы не отправлялись.
- C# backend имеет 498 `[RemoteEvent]` атрибутов в 137 файлах: нужен пофайловый security review, особенно авторизация, экономика, инвентарь и платежи. Текущий счётчик — ориентир, не доказательство качества обработчиков.

## Ключевые неизвестные

- Какая версия RAGE:MP и C# bootstrapper обязательна для этого исходника?
- Какой порядок импорта SQL и как реализуются миграции/инициализация данных?
- Какие сервисы обязательны помимо MySQL (Redis, website/auth/payment endpoints, voice)?
- Какие client packages/assets соответствуют исходникам и как устроена генерация production bundle?
- Какие разрешения владельца относятся к шрифтам, MLO/DLC и прочим сторонним ресурсам?
