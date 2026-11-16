# GitHub-инструменты и правила разработки Gastronomy

## 1. Что включаем

| Инструмент | Решение | Польза |
|---|---|---|
| Branches + Pull Requests | Обязательно | Изоляция изменений и review |
| Issues | Обязательно | Задачи с критериями готовности |
| Projects | Рекомендуется | Kanban и roadmap, связанный с Issues/PR |
| Actions | Обязательно | CI при изменениях |
| Dependabot | Обязательно | Обновления npm/pnpm и GitHub Actions |
| Security / dependency alerts | Включить | Уязвимости зависимостей |
| CodeQL | Включить после появления кода приложения | Статический анализ поддерживаемых языков |
| Discussions | Пока нет | На старте хватает Issues |
| Wiki | Нет | Документация хранится в docs/ рядом с кодом |
| Releases | Позже | Когда появятся пилотные версии |
| GitHub Pages | Не для приложения | Не основной runtime для full-stack Next.js |
| Codespaces | Опционально | Удобно для подключения разработчиков |
| Packages | Не сейчас | Собственный registry не нужен |

Ссылки:
- Projects: https://docs.github.com/en/issues/planning-and-tracking-with-projects
- Actions CI: https://docs.github.com/en/actions/tutorials/build-and-test-code/nodejs
- Dependabot: https://docs.github.com/en/code-security/dependabot/dependabot-version-updates
- CodeQL: https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql

## 2. Ветки

- main — стабильная ветка.
- feat/<name> — функциональность.
- fix/<name> — исправления.
- docs/<name> — документация.
- chore/<name> — инфраструктура.

Правила:
- не коммитить напрямую в main;
- одна логическая задача — один PR;
- PR содержит описание, критерии приёмки, тесты и скриншоты UI при необходимости;
- CI должен быть зелёным;
- не включать auto-merge;
- изменения исторических материалов требуют отдельного обоснования.

## 3. Labels

Предлагаемые метки:
- type:feature, type:bug, type:docs, type:chore, type:research;
- priority:P0, priority:P1, priority:P2;
- area:frontend, area:backend, area:database, area:auth, area:moderation, area:analytics, area:infra;
- status:blocked, status:needs-review.

## 4. Минимальный CI

На pull_request и push в рабочие ветки:
1. установить закреплённую версию Node LTS;
2. настроить pnpm;
3. установить зависимости строго по lockfile;
4. lint;
5. typecheck;
6. unit tests;
7. build;
8. Playwright smoke E2E после появления стабильной тестовой среды.

Фиксировать версии GitHub Actions, обновлять через Dependabot. Секреты не хранить в файлах репозитория.

## 5. PR checklist

Каждый PR отвечает на вопросы:
1. Что изменено и зачем?
2. Как проверить?
3. Какие риски и миграции?
4. Какие скриншоты/видео показывают результат?
5. Какие задачи закрывает?

## 6. Definition of Ready / Done

**Ready:** описана пользовательская проблема, сценарий, приоритет, критерии приёмки, дизайн/API-контракт при необходимости.

**Done:** код, тесты, документация, CI, отсутствие критических дефектов, PR reviewed, результат продемонстрирован. Для функций с данными проверены права доступа, ошибки, удаление и аудит.

## 7. Особенности текущего Gastronomy

В main обнаружены большие исторические каталоги Recipes/, RedAge-3.0/, community/ и архив. Их не удалять и не смешивать с новым приложением. Новый продукт размещать в apps/web/, документацию — в docs/. Материалы из старых каталогов не импортировать автоматически в публичный продукт: сначала проверить происхождение, права и назначение.
