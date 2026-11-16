import Link from "next/link";
import { ArrowRight, Award, ChefHat, Flame } from "lucide-react";

export default function ProfilePage() {
  return (
    <main className="shell page-shell profile-shell">
      <span className="section-index">ПРОФИЛЬ УЧАСТНИКА</span>
      <div className="profile-card">
        <div className="profile-avatar"><ChefHat size={32} /></div>
        <div><span className="eyebrow">ДЕМО-ПРОФИЛЬ</span><h1>Домашний кулинар</h1><p>Здесь появятся ваши публикации, достижения и история участия.</p></div>
      </div>
      <div className="profile-stats"><div><Award size={20} /><strong>0 XP</strong><span>Накоплено</span></div><div><Flame size={20} /><strong>0</strong><span>Заданий завершено</span></div></div>
      <div className="empty-panel"><h2>Ваша первая история начинается здесь</h2><p>Выберите задание и приготовьте что-нибудь новое.</p><Link className="text-link" href="/challenges">Посмотреть задания <ArrowRight size={16} /></Link></div>
    </main>
  );
}
