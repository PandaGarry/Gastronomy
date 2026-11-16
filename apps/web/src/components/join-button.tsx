"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Check, Plus } from "lucide-react";

export function JoinButton({ slug, className = "" }: { slug: string; className?: string }) {
  const [joined, setJoined] = useState(false);

  if (joined) {
    return (
      <div className="join-success">
        <span><Check size={17} /> Вы участвуете</span>
        <Link className="text-link" href={`/challenges/${slug}/submit`}>Опубликовать результат <ArrowRight size={15} /></Link>
      </div>
    );
  }

  return (
    <button
      className={`button button-primary ${className}`}
      type="button"
      onClick={() => setJoined(true)}
    >
      <Plus size={17} />
      Присоединиться
    </button>
  );
}
