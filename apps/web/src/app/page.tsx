import Link from "next/link";
import { ArrowDown, ArrowRight, ChefHat, Heart, Sparkles, Trophy } from "lucide-react";
import { ChallengeCard } from "@/components/challenge-card";
import { challenges } from "@/lib/challenges";

export default function HomePage() {
  const featured = challenges[0];

  return (
    <main>
      <section className="hero shell">
        <div className="hero-copy">
          <span className="kicker"><Sparkles size={15} /> Новая привычка — готовить интереснее</span>
          <h1>Не просто готовьте.<br /><em>Открывайте новое.</em></h1>
          <p className="hero-description">Небольшие кулинарные задания превращают обычную готовку в повод попробовать что-то новое, поделиться результатом и вдохновиться другими.</p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/challenges">Выбрать задание <ArrowRight size={17} /></Link>
            <a className="button button-quiet" href="#how-it-works">Как это работает</a>
          </div>
          <div className="hero-proof"><span className="proof-icon"><Heart size={16} /></span><span>Для любителей домашней кухни.<br /><strong>Без гонки за идеальностью.</strong></span></div>
        </div>
        <div className="hero-visual">
          <div className="hero-photo hero-photo-main"><span className="photo-caption">Ваш следующий кулинарный эксперимент</span><span className="photo-orb" /></div>
          <div className="floating-note"><span className="note-icon"><Trophy size={18} /></span><span><strong>+120 XP</strong><small>за одобренный результат</small></span></div>
          <div className="hero-side-label">СЕЗОН ВКУСНЫХ ОТКРЫТИЙ · 01</div>
        </div>
        <a className="scroll-cue" href="#how-it-works"><ArrowDown size={15} /> Листайте, чтобы узнать</a>
      </section>

      <section className="intro-strip" id="how-it-works">
        <div className="shell intro-grid">
          <div><span className="section-index">01 / ИДЕЯ</span><h2>Готовка становится<br />маленьким приключением.</h2></div>
          <p>Выбирайте тему, готовьте в своём ритме и показывайте, что получилось. Здесь важен не ресторанный идеал, а любопытство, практика и удовольствие от процесса.</p>
          <div className="steps-mini"><span><b>01</b> Выберите задание</span><span><b>02</b> Приготовьте</span><span><b>03</b> Поделитесь</span></div>
        </div>
      </section>

      <section className="section shell">
        <div className="section-heading"><div><span className="section-index">02 / ПОПРОБУЙТЕ</span><h2>Задания недели</h2><p>Выберите то, что подходит именно сегодня.</p></div><Link className="text-link" href="/challenges">Все задания <ArrowRight size={16} /></Link></div>
        <div className="challenge-grid">{challenges.map((challenge, index) => <ChallengeCard key={challenge.slug} challenge={challenge} featured={index === 0} />)}</div>
      </section>

      <section className="closing-band"><div className="shell closing-inner"><div><span className="section-index">ВАШ ХОД</span><h2>Один рецепт.<br /><em>Много новых историй.</em></h2></div><Link className="button button-light" href="/challenges">Найти своё задание <ArrowRight size={17} /></Link></div></section>
    </main>
  );
}
