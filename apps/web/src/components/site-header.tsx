import Link from "next/link";
import { ChefHat, CircleUserRound, Compass, House, Trophy } from "lucide-react";

const links = [
  { href: "/", label: "Главная", icon: House },
  { href: "/challenges", label: "Задания", icon: Compass },
];

export function SiteHeader() {
  return (
    <>
      <header className="site-header">
        <Link className="brand" href="/" aria-label="На главную">
          <span className="brand-mark"><ChefHat size={20} strokeWidth={2.2} /></span>
          <span className="brand-copy"><strong>Кулинарная лига</strong><small>Готовьте. Пробуйте. Делитесь.</small></span>
        </Link>
        <nav className="desktop-nav" aria-label="Основная навигация">
          {links.map(({ href, label }) => <Link key={href} href={href}>{label}</Link>)}
          <a href="#how-it-works">Как это работает</a>
        </nav>
        <div className="header-actions">
          <Link className="button button-quiet button-small" href="/challenges">Найти задание</Link>
          <Link className="avatar-link" href="/profile" aria-label="Демо-профиль"><CircleUserRound size={21} /></Link>
        </div>
      </header>
      <nav className="mobile-nav" aria-label="Мобильная навигация">
        <Link href="/"><House size={19} /><span>Главная</span></Link>
        <Link href="/challenges"><Compass size={19} /><span>Задания</span></Link>
        <Link href="/profile"><Trophy size={19} /><span>Профиль</span></Link>
      </nav>
    </>
  );
}
