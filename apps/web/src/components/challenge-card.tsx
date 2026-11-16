import Link from "next/link";
import { ArrowUpRight, Clock3, Flame, Users } from "lucide-react";
import type { Challenge } from "@/lib/challenges";

export function ChallengeCard({ challenge, featured = false }: { challenge: Challenge; featured?: boolean }) {
  return (
    <article className={`challenge-card ${featured ? "challenge-card-featured" : ""}`}>
      <Link className={`challenge-art art-${challenge.accent}`} href={`/challenges/${challenge.slug}`} aria-label={`Открыть задание: ${challenge.title}`}>
        <span className="art-label">{challenge.imageLabel}</span>
        <span className="art-orbit art-orbit-one" />
        <span className="art-orbit art-orbit-two" />
        <span className="art-stamp">{challenge.xp} XP</span>
      </Link>
      <div className="challenge-card-body">
        <div className="eyebrow-row"><span className="eyebrow">{challenge.category}</span><span className="difficulty">{challenge.difficulty}</span></div>
        <h3><Link href={`/challenges/${challenge.slug}`}>{challenge.title}</Link></h3>
        <p>{challenge.description}</p>
        <div className="challenge-meta">
          <span><Clock3 size={14} />{challenge.time}</span>
          <span><Users size={14} />{challenge.participants}</span>
          <span><Flame size={14} />{challenge.deadline}</span>
        </div>
        <Link className="text-link" href={`/challenges/${challenge.slug}`}>Подробнее <ArrowUpRight size={15} /></Link>
      </div>
    </article>
  );
}
