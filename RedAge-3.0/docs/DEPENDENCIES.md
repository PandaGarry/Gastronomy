# Инвентаризация зависимостей и сборки

Снято с текущего авторизованного source snapshot, commit `23730b8cd464f86c47eaae6f80d182cd651092b2`. Пакетные версии ниже — декларации репозитория; они ещё не подтверждены чистой повторяемой сборкой.

## Серверная часть

| Компонент | Объявленная версия | Где используется / замечание |
|---|---|---|
| Target framework | `netcoreapp3.1` | `NeptuneEvo`, `NeptuneEvoSDK`, `Localization`; требуется совместимость с конкретной версией RAGE:MP. .NET Core 3.1 давно вне поддержки. |
| linq2db.MySql | 3.3.0 | ORM / MySQL provider. |
| MySql.Data | 8.0.28 | Старый Oracle MySQL provider, в том числе используется `BackupSql`. |
| MySqlBackup.NET | 2.3.4 | Экспорт backup. |
| MySqlConnector | 1.1.0 | Используется основным SDK/backend; connection strings сейчас отключают TLS. |
| Newtonsoft.Json | 12.0.3 | JSON сериализация. |
| Otp.NET | 1.2.2 | OTP/2FA. |
| StackExchange.Redis | 2.2.79 | Redis integration. |
| System.Data.SQLite.Core | 1.0.113.7 / 1.0.110 | Разные версии заданы в `NeptuneEvo` и `NeptuneEvoSDK`; проверить resolution/native assets на чистой сборке. |
| Bootstrapper | `Bootstrapper.dll` без package version | Локальная binary reference; нужно установить происхождение, версию и соответствие RAGE runtime. |

NuGet lockfile/CI matrix в текущем snapshot не найден; версии SDK и runtime не зафиксированы в воспроизводимой build pipeline.

## Клиент JavaScript

- Manifest: webpack CLI `^4.9.1`, webpack `^5.66.0`; lockfile отсутствует.
- Команда `build` явно включает production mode.
- Изолированная сборка прошла на Node 22 с `NODE_OPTIONS=--openssl-legacy-provider`; временный resolver выбрал webpack 5.112.2.
- Результат не закреплён lockfile и не является подтверждённой целевой версией RAGE:MP client runtime.

## CEF/Svelte UI

- Svelte `^3.48.0`, `svelte-loader` `2.13.3`, webpack `5.21.0`, webpack-cli `^3.3.11`, webpack-dev-server `^4.9.0`, Sass `^1.58.3`.
- В manifest одновременно есть cache-loader `^4.1.0` (peer ожидает webpack 4) и webpack 5.21.0; clean npm install закономерно останавливается на ERESOLVE.
- Script `build` не задаёт `NODE_ENV=production`; `webpack.config.js` по умолчанию выставляет development mode и source maps. `buildtest`/`builden` также используют те же mode checks.
- Пакеты `request`, старые webpack plugins/loaders, `core-js`/`uuid` transitive dependencies и другие deprecated packages требуют inventory/upgrade, но только после фиксации lockfile и тестов.
- Временный npm audit из свежего registry resolution: 49 advisories (5 critical, 21 high, 22 moderate, 1 low). Это не upstream lock и не verdict о production exploitability.
- Все три конфигурации пишут в `client_packages/interface`; localized RU/EN configs ссылаются на внешний CDN host. Проверить, кому он принадлежит и что должен содержать новый deployment.

## Тесты

- В package scripts нет `test`-команд; в snapshot обнаружены только два файла с именем `test.js`, их назначение пока не классифицировано.
- C# test project не обнаружен; SQL integration тестов и CI pipeline пока не найдено.
- Нужен план: unit/integration tests для server service layer + тестовый MySQL; smoke tests для клиента и RAGE lifecycle.
