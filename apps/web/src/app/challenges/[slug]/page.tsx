import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, CheckCircle2, Clock3, Coins, Flame, Users } from "lucide-react";
import { JoinButton } from "@/components/join-button";
import { getChallenge } from "@/lib/challenges";

export function generateStaticParams() {
  return [{ slug: "perfect-breakfast" }, { slug: "seasonal-vegetables" }, { slug: "comfort-food" }];
}

export default async function ChallengeDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const challenge = getChallenge(slug);
  if (!challenge) notFound();

  return (
    <main className="shell detail-shell">
      <Link className="back-link" href="/challenges"><ArrowLeft size={16} /> Все задания</Link>
      <div className="detail-layout">
        <div>
          <div className={`detail-art art-${challenge.accent}`}><span className="art-label">{challenge.imageLabel}</span><span className="art-orbit art-orbit-one" /><span className="art-orbit art-orbit-two" /><span className="art-stamp">{challenge.xp} XP</span></div>
          <div className="detail-copy">
            <span className="eyebrow">{challenge.category} · {challenge.difficulty}</span>
            <h1>{challenge.title}</h1>
            <p className="detail-lead">{challenge.description}</p>
            <h2>Ваша задача</h2>
            <p>Приготовьте собственную версию блюда, уделив внимание вкусу и подаче. Не нужно повторять чужую работу — интереснее увидеть вашу интерпретацию.</p>
            <h2>Что понадобится</h2>
            <ul className="ingredient-list">{challenge.ingredients.map((item) => <li key={item}><CheckCircle2 size={17} />{item}</li>)}</ul>
            <h2>Как выполнить</h2>
            <ol className="step-list">{challenge.steps.map((step) => <li key={step}>{step}</li>)}</ol>
          </div>
        </div>
        <aside className="join-panel">
          <span className="section-index">ВАШЕ УЧАСТИЕ</span>
          <h2>Попробуете?</h2>
          <p>Присоединяйтесь и возвращайтесь, когда результат будет готов.</p>
          <div className="challenge-facts"><span><Clock3 size={16} />Время <strong>{challenge.time}</strong></span><span><Coins size={16} />Бюджет <strong>{challenge.budget}</strong></span><span><Flame size={16} />Награда <strong>{challenge.xp} XP</strong></span><span><Users size={16} />Участники <strong>{challenge.participants}</strong></span></div>
          <JoinButton className="join-full" />
          <small className="prototype-note">Действие демонстрационное: участие не сохраняется на сервере.</small>
        </aside>
      </div>
    </main>
  );
}
