import { Search, SlidersHorizontal } from "lucide-react";
import { ChallengeCard } from "@/components/challenge-card";
import { challenges } from "@/lib/challenges";

export default function ChallengesPage() {
  return (
    <main className="shell page-shell">
      <div className="page-heading"><span className="section-index">КОЛЛЕКЦИЯ ЗАДАНИЙ</span><h1>Что приготовим?</h1><p>Выберите идею по настроению, времени и уровню сложности.</p></div>
      <div className="catalog-toolbar">
        <label className="search-field"><Search size={17} /><input type="search" placeholder="Найти задание" aria-label="Найти задание" /></label>
        <button className="button button-quiet filter-button" type="button"><SlidersHorizontal size={16} /> Фильтры</button>
      </div>
      <div className="filter-chips"><span className="filter-chip active">Все задания</span><span className="filter-chip">Быстро · до 30 мин</span><span className="filter-chip">Для начинающих</span><span className="filter-chip">До 500 ₽</span></div>
      <div className="catalog-count">Открытые задания <strong>{challenges.length}</strong></div>
      <div className="challenge-grid">{challenges.map((challenge) => <ChallengeCard key={challenge.slug} challenge={challenge} />)}</div>
      <p className="prototype-note">Демо-данные для проверки интерфейса. Поиск и фильтры пока визуальные и не подключены к серверу.</p>
    </main>
  );
}
