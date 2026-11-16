import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Camera } from "lucide-react";
import { SubmissionComposer } from "@/components/submission-composer";
import { getChallenge } from "@/lib/challenges";

export default async function SubmitPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const challenge = getChallenge(slug);
  if (!challenge) notFound();

  return (
    <main className="shell submit-shell">
      <Link className="back-link" href={`/challenges/${slug}`}><ArrowLeft size={16} /> К заданию</Link>
      <div className="submit-heading"><span className="section-index"><Camera size={14} /> ВАШ РЕЗУЛЬТАТ</span><h1>Покажите, что получилось.</h1><p>Задание: <strong>{challenge.title}</strong></p></div>
      <SubmissionComposer challengeTitle={challenge.title} />
    </main>
  );
}
