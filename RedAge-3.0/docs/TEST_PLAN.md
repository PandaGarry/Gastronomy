# Проверки и результаты

Последнее обновление: 2026-11-07. Это baseline текущего исходного снимка; production-тесты не выполнялись.

## Среда

- Node.js: `v22.22.3`
- npm: `10.9.8`
- .NET SDK/MSBuild/Mono: отсутствуют
- MySQL/MariaDB client/server: отсутствуют
- Доступная RAM в sandbox: около 3.8 GiB; большие webpack jobs завершаются OOM/exit 137
- Полный RAGE:MP runtime/server binaries: не включены в рабочий snapshot

## Baseline

| Проверка | Статус | Результат / ограничение |
|---|---|---|
| JSON синтаксис | Пройдено | Проверены 167 JSON-файлов: 167 валидны. Значения секретов не печатались; DB-конфиг локально редактирован. |
| JavaScript syntax | Частично пройдено | Из 337 `.js`: 335 проходят `node --check`. 2 ошибки в файлах, не подключённых из текущих entry points: `src_client/synchronization/sit1asdas.js` (повторное объявление `sitData`) и `src_cef/src/views/player/hudevo/phonenew/map.js` (лишняя запятая перед `;`). Активный `src_client/index.js` и `synchronization/sit.js` проходят. Не исправлял до выяснения назначения старых файлов. |
| Client webpack build | Пройдено в изолированной копии | Временная копия `src_client`; npm install с отключёнными lifecycle scripts; `NODE_OPTIONS=--openssl-legacy-provider`; production bundle собран успешно (webpack 5.112.2). Артефакт не переносился в исходник. Нет upstream lockfile, поэтому это не воспроизводимый pin. |
| CEF npm dependency resolution | Требует исправления | Обычный `npm install` остановлен `ERESOLVE`: `cache-loader@4.1.0` требует peer webpack 4, а manifest фиксирует webpack 5. Установка прошла только с `--legacy-peer-deps`. |
| CEF dependency audit | Высокий риск / требует triage | Временная свежая установка из manifest (не upstream lock) получила 49 npm audit advisories: 5 critical, 21 high, 22 moderate, 1 low. Среди прямых пакетов отмечены `request`, `webpack`, iconfont-related plugins. Это не автоматически означает runtime-эксплуатацию; нужно разобрать, какие пакеты реально используются при сборке/в игре, и составить обновление. |
| CEF/Svelte build | Заблокировано окружением/неполнотой снимка | С неполным snapshot build проходит компиляцию модулей, затем сообщает ошибки из-за намеренно исключённых image/font/media assets (1256 ошибок; также Svelte a11y/deprecation warnings). Для проверки полностью получены assets только во временную папку; production webpack завершился OOM/exit 137 при лимите памяти sandbox. Исходные файлы не менялись. Нужен CI/host с большей RAM и проверка чистого полного набора. |
| C# build | Заблокировано | В среде отсутствуют .NET SDK/MSBuild; проект target `netcoreapp3.1`. Npm/PyPI install не дал доступного SDK. Нужен контролируемый build-agent и проверка совместимости RAGE:MP. |
| C# static syntax parse | Частичный эксперимент | Tree-sitter C# разобрал 558 файлов; полный parse дал error flag для 5 крупных файлов (`Main.cs`, `Chars/Repository.cs`, `Core/Commands.cs`, `Fractions/Manager.cs`, `Jobs/Miner.cs`), но без полноценного compiler/parser triage нельзя отличить грамматические ограничения от реальных errors. Изменённые `IsReadOnlyOpenedTent`/`ItemsMoveStack` и `ItemsMove` snippets отдельно распарсились без syntax-tree errors; это не заменяет compile. |
| SQL import | Заблокировано | Нет MySQL/MariaDB. Файлы имеют MySQL-specific `DELIMITER` stored procedures; generic parser не заменяет настоящий импорт. В test DB ещё не загружались. |
| DB transport/config review | Статический риск | Connection strings отключают TLS (`SslMode=None`), startup выполняет `SET GLOBAL max_connections=500`; оба пункта заведены в `ISSUES.md`, тестовый DB-профиль ещё не выбран. |
| RAGE:MP smoke test | Заблокировано | Не включены runtime/server binaries, полный `client_packages` и тестовый игровой сервер. Не запускал неизвестные бинарники. |
| Нагрузочный тест | Ожидает | Нужны стабильно собираемый staging и согласованный профиль нагрузки/метрики. |

## Правила выполнения

- Не запускать production binaries и не подключать production DB из этого sandbox.
- Сначала статические проверки; SQL — только на одноразовой тестовой БД.
- Любой credential считать скомпрометированным, если он попал в публичный upstream; сменить его у владельца.
- Сохранять версии toolchain, команды, exit status и ограничения; dependency audit проводить на зафиксированном lockfile.
- Build, успешный только с временными флагами/неполными зависимостями, помечать experimental, не выдавать за воспроизводимый release build.

## Следующие наборы тестов после подготовки staging

1. **Auth/passwords:** legacy hash verify, безопасный KDF rehash/reset, Unicode, неверный пароль, повторные/параллельные попытки, отсутствие секретов в логах.
2. **Queue/concurrency:** много одновременных auth/connect/disconnect событий при заполненных слотах; нет duplicate entry, lost player, race exception или обхода rate limit.
3. **Economy/payments:** только sandbox endpoints; сценарии `ECONOMY_REVIEW.md` + `PAYMENTS_REVIEW.md` + `ROULETTE_REVIEW.md` + `CASINO_REVIEW.md` + `BLACKJACK_REVIEW.md`: offline/online RedBucks receiver, DB failure/rollback, replay transfer callback, concurrent money-worker producers, receipt duplicate/crash-before-ack, multi-worker overlap, promo dedupe, DonatePack invalid ID/restart/delayed payment, malformed ATM args и overflow; roulette buy/open negative/zero/over-limit counts, checked price overflow, discount and item/wallet consistency; NewCasino Roulette forged last-bet cancel around `table.Process`, exposed outcome payload, disconnect/death/timeout within and outside the five-second refund grace, exactly-once round settlement; Blackjack invalid table/seat and forged-coordinate joins, repeated setBet, out-of-turn/invalid split/double, server max-bet and payout overflow cases. Проверять exactly-once ledger, affected rows, cache consistency и отсутствие ложных success notifications; в `BuySet` искусственно заполнять inventory перед каждым шагом выдачи и сверять debit/full reward/compensation.
4. **Inventory:** direct remote fuzz для отрицательных/нулевых/over-source counts и same-slot; все transfer/use/drop из чужих tent/read-only containers; stack/carry caps/full-source move; tampered/duplicate NoteCreate IDs; roulette negative case-open count and `RemoveIndex` no-op for nonpositive count; reconnect; затем DB outage/restart и сверка каждого item SQL ID/count. Подробно: `INVENTORY_REVIEW.md`.
5. **DB lifecycle:** чистый импорт, повторный импорт только если заявлен idempotent, backup→restore, least-privilege DB user, TLS.
6. **Release packaging:** повторяемые clean builds, `meta.xml` указывает на фактический Release artifact, правильные client bundles/assets, rollback artefacts.
