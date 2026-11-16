"use client";

import { useState } from "react";
import { Check, Plus } from "lucide-react";

export function JoinButton({ className = "" }: { className?: string }) {
  const [joined, setJoined] = useState(false);

  return (
    <button
      className={`button ${joined ? "button-joined" : "button-primary"} ${className}`}
      type="button"
      onClick={() => setJoined((value) => !value)}
      aria-pressed={joined}
    >
      {joined ? <Check size={17} /> : <Plus size={17} />}
      {joined ? "Вы участвуете" : "Присоединиться"}
    </button>
  );
}
