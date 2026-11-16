# Основы дизайн-системы v0.1

Статус: начальные UX/UI-токены и правила для web-прототипа. Не финальный визуальный бренд. Название и айдентика продукта не утверждены.

## 1. Визуальное направление

Направление: современная редакционная гастрономия + дружелюбная игровая среда. Не детский геймифицированный интерфейс, не маркетплейс и не типовой dashboard.

- Фотография блюда — главный визуальный носитель.
- Чистая типографика и ясная иерархия.
- Тёплые нейтральные поверхности; один выразительный акцент для главного действия.
- XP/бейджи показывать дозированно и объяснять смысл.
- Избегать кислотных градиентов, визуального шума, бесконечных карточек и декоративных графиков.
- Контент должен выглядеть достоверно: не использовать искусственные фото как доказательства пользовательских результатов.

## 2. Цветовые роли

Цветовые значения — временные design tokens, не брендовые обязательства. Реализовать через CSS variables и semantic tokens.

| Token | Назначение |
|---|---|
| background | основной фон |
| foreground | основной текст |
| surface | карточки и панели |
| surface-muted | вторичные поверхности |
| border | разделители и обводки |
| primary | главное действие |
| primary-foreground | текст на primary |
| accent | вспомогательный акцент/XP |
| success | одобрение и успешные состояния |
| warning | ожидание/предупреждение |
| destructive | ошибка, удаление, блокировка |
| muted-foreground | вторичный текст |

Контраст текста и интерактивных элементов проверять по WCAG 2.2 AA; цвет не должен быть единственным способом передать статус.

## 3. Типографика и ритм

- Использовать системный sans-serif стек на старте; не загружать внешний шрифт до выбора лицензии и хостинга.
- Заголовки: короткие, с ясной иерархией.
- Основной текст: комфортная ширина строки 60–75 символов.
- Базовая сетка spacing: 4 px; компоненты используют кратные значения.
- Радиусы: небольшие/средние, без чрезмерно округлого «игрушечного» вида.
- Минимальная высота интерактивной цели — 44 px на touch.
- Анимации короткие и функциональные; учитывать prefers-reduced-motion.

## 4. Компонентный инвентарь

### Foundation
Button, IconButton, Link, Input, Textarea, Select, Checkbox, Radio, Switch, Badge, Avatar, Separator, Tooltip, Dialog, Dropdown, Tabs, Toast, Skeleton, Alert, EmptyState, ErrorState, Pagination.

### Product
ChallengeCard, ChallengeStatus, DifficultyBadge, TimeBudgetMeta, ParticipationButton, ParticipationStatus, SubmissionComposer, MediaUploader, MediaPreview, SubmissionCard, ModerationStatus, XPBadge, XPProgress, AchievementCard, ReactionBar, ReportDialog, UserSummary, NotificationItem.

### Admin/moderation
AdminTable, FilterBar, ModerationQueueItem, ModerationDecisionPanel, ReasonSelector, AuditTimeline, RoleBadge, UserRestrictionDialog.

## 5. Состояния компонентов

Button: default, hover, focus-visible, active, loading, disabled.
Input: default, focus, invalid, disabled, read-only.
Uploader: idle, drag-over, uploading, uploaded, failed, rejected-format, too-large.
ChallengeCard: open, scheduled, paused, full, completed, archived.
Submission: draft, pending, approved, changes-requested, rejected, hidden.
Notification: unread, read.
Dialog: open, submitting, error, success.

## 6. Responsive behavior

- Mobile: 320–767 px; одна колонка, bottom navigation, полноширинные основные действия.
- Tablet: 768–1023 px; 1–2 колонки в зависимости от контента.
- Desktop: 1024 px+; основная колонка и необязательная контекстная панель.
- Не использовать горизонтальный скролл для основного контента.
- В редакторе публикации фото должны удобно добавляться с камеры/галереи; поля не должны терять введённый текст при ошибке сети.
- Таблицы админки на мобильных преобразовывать в карточки или отдельные detail views.

## 7. Фотоконтент

- Пропорции карточки не должны обрезать само блюдо агрессивно.
- Для пользовательских изображений предусмотреть placeholder, blur/low-res preview и lazy loading.
- Alt text доступен для значимых изображений; декоративные изображения имеют пустой alt.
- Не использовать изображения, вводящие в заблуждение относительно реальных результатов участников.
- Не показывать EXIF/геолокацию и приватные URL оригиналов.

## 8. Доступность и тестирование

- Клавиатурная навигация и focus-visible.
- Семантические заголовки и landmarks.
- Labels для всех полей, понятные ошибки.
- Диалоги управляют focus и закрываются ожидаемым способом.
- Проверка reduced motion.
- Проверка контраста и масштабирования 200%.
- Минимальный smoke-test ключевых сценариев на мобильном viewport и desktop.

## 9. Не входит в v0.1
Логотип, финальная палитра бренда, иллюстративный стиль, маркетинговые визуалы и окончательные фотографии. Их создавать после определения позиционирования и названия.
