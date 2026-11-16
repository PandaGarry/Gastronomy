# Техническая архитектура Gastronomy v0.1

Статус: рекомендация для интерактивного MVP-прототипа, 16.11.2026. Это план, не описание уже реализованного приложения.

## 1. Рекомендуемый стек

| Слой | Выбор | Причина |
|---|---|---|
| Язык | TypeScript | Типизация на клиенте и сервере |
| Framework | Next.js App Router + React | Full-stack web, SSR, server actions/route handlers |
| UI | Tailwind CSS + официальный shadcn/ui | Быстрый старт, доступные компоненты, полный контроль над исходниками |
| Иконки | lucide-react | Единая библиотека |
| Формы | React Hook Form + Zod | Сложные формы и общая схема валидации |
| База | PostgreSQL | Надёжная реляционная модель |
| ORM | Drizzle ORM + Drizzle Kit | Типизированная схема и SQL-миграции |
| Auth | Better Auth | Email/password и сессии; без OAuth на первом этапе |
| Тесты | Vitest + Testing Library + Playwright | Unit/component и браузерные E2E |
| Пакетный менеджер | pnpm | Lockfile и воспроизводимые установки |
| CI | GitHub Actions | Автоматические проверки PR |
| Файлы | S3-compatible object storage | Фотографии блюд с подписанной загрузкой |
| Локальная среда | Docker Compose | PostgreSQL и локальное S3-совместимое хранилище |
| Деплой | Docker на выбранном российском провайдере | Контроль расположения данных и переносимость |

Официальные руководства:
- Next.js App Router: https://nextjs.org/docs/app
- Next.js deployment: https://nextjs.org/docs/app/getting-started/deploying
- shadcn/ui: https://ui.shadcn.com/docs/installation/next
- Drizzle + PostgreSQL: https://orm.drizzle.team/docs/get-started/postgresql-new
- Better Auth: https://better-auth.com/docs/installation
- Playwright: https://playwright.dev/docs/intro
- Vitest: https://vitest.dev/guide/

## 2. Архитектурный стиль

**Модульный монолит.** Один Next.js application с доменными модулями. Не строить микросервисы, GraphQL, event bus или Kubernetes на старте.

Поток запроса: UI → Server Action / Route Handler → auth + Zod validation + authorization → domain service → Drizzle repository → PostgreSQL / object storage.

Бизнес-правила XP, прав доступа, модерации и публикации должны жить на сервере, а не в клиентском интерфейсе.

## 3. Изоляция нового приложения в репозитории

В текущем main обнаружены исторические каталоги Recipes/, RedAge-3.0/, community/ и архив. Не удалять, не переименовывать и не смешивать их с новым продуктом.

Новый продукт разместить в apps/web/. Документы — в docs/. На первом этапе не нужен Turborepo: приложение одно. pnpm workspace имеет смысл включить, когда появятся дополнительные пакеты.

Предлагаемая структура:

    Gastronomy/
    ├── apps/web/
    │   ├── src/app/
    │   ├── src/components/ui/
    │   ├── src/components/shared/
    │   ├── src/features/auth/
    │   ├── src/features/challenges/
    │   ├── src/features/submissions/
    │   ├── src/features/profile/
    │   ├── src/features/gamification/
    │   ├── src/features/moderation/
    │   ├── src/features/admin/
    │   ├── src/server/db/
    │   ├── src/server/storage/
    │   ├── drizzle/
    │   ├── tests/
    │   └── package.json
    ├── docs/
    └── .github/

## 4. Доменные модули MVP

### P0 — обязательное ядро
- Auth & Profile: регистрация, вход, псевдоним, аватар, приватность, роли.
- Challenges: каталог заданий, фильтры, правила, даты, сложность, время и бюджет.
- Participation: присоединение и выход, статусы участия.
- Submissions: 1–3 фотографии, заметка, черновик, отправка на модерацию.
- Feed & Reactions: лента внутри задания, простые реакции, ограниченные комментарии.
- Gamification: серверное начисление XP, личный прогресс, достижения.
- Moderation: жалобы, скрытие/восстановление контента, блокировки, журнал действий.
- Admin: создание заданий, модерация, управление аккаунтами, базовая статистика.
- Analytics events: измерение ключевого пользовательского цикла.

### P1 — после подтверждения P0
Приватные дуэли, команды, сезоны, персональные рекомендации, расширенная история, голосования.

### Не строить сейчас
AI-генерацию и распознавание еды, pantry, meal planning, покупки, marketplace, платежи, денежную валюту, открытые личные сообщения, глобальные рейтинги, нативные приложения, WebSockets.

## 5. Начальная модель данных

Минимальные сущности:
- users, profiles;
- challenges, challenge_participations;
- submissions, media_assets;
- reactions, comments, reports;
- moderation_actions;
- xp_ledger;
- achievements, user_achievements;
- analytics_events.

XP начисляется только сервером после одобрения результата. Использовать транзакцию и уникальный ключ идемпотентности, чтобы повторный запрос не начислял очки дважды. Не доверять значению XP, присланному клиентом.

## 6. Фотографии и UGC

- Разрешать только проверенные форматы и MIME-типы; проверять фактическое декодирование.
- Ограничивать размер, число файлов и частоту загрузок.
- Загружать через короткоживущие pre-signed URLs.
- Исходники хранить приватно; публичную выдачу делать контролируемой.
- Удалять EXIF, если метаданные не нужны.
- Не исполнять пользовательские файлы и не отдавать их с origin приложения.
- Ручная модерация в пилоте; жалобы и журнал действий обязательны.
- Не использовать распознавание лиц или еды в MVP.

## 7. Безопасность и персональные данные

Минимизировать собираемые данные; для пилота рассмотреть подтверждение 18+ без хранения полной даты рождения. Все проверки ролей и прав — на сервере. Секреты — только в переменных окружения и GitHub Secrets. Настроить rate limiting, резервное копирование и проверку восстановления.

Для персональных данных граждан РФ проектировать первичное хранение, резервные копии, файлы, логи и аналитику с учётом требований локализации. До публичного запуска юридически проверить основания обработки, согласия, политику, пользовательское соглашение, UGC-правила и удаление данных. Это техническая карта, не юридическое заключение.

## 8. Аналитика

События: signup_completed, challenge_viewed, challenge_joined, submission_started, submission_published, submission_approved, reaction_added, comment_added, challenge_completed, second_challenge_joined, invite_accepted, report_created, moderation_action.

Писать события на сервере с псевдонимизированным user ID, timestamp, challenge ID, UTM/source и cohort. Не передавать в аналитику email, телефон и тексты пользовательских сообщений.

## 9. Что отложить

| Технология | Сейчас | Вернуться, когда |
|---|---|---|
| Redis | Нет | Появятся подтверждённые проблемы с очередями, кэшем или распределённым rate limit |
| BullMQ | Нет | Понадобится массовая фоновая обработка |
| WebSockets | Нет | Реальные live-дуэли потребуют мгновенной синхронизации |
| OpenSearch | Нет | PostgreSQL перестанет справляться с поиском |
| Kubernetes | Нет | Появятся несколько сервисов и операционная команда |
| GraphQL | Нет | Несколько клиентов потребуют сложного API |
| AI API | Нет | Подтвердится конкретный пользовательский сценарий и экономика |

## 10. Definition of Done технического прототипа

Проект запускается по README на чистой машине; миграции воспроизводимы; seed создаёт демо-данные; пользователь проходит регистрацию → задание → участие → публикацию → модерацию → XP; роли проверяются сервером; повторное начисление XP невозможно; unit и E2E тесты проходят; CI зелёный; секретов нет в репозитории; процедура backup/restore документирована.
