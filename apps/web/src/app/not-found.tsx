import Link from "next/link";

export default function NotFound() {
  return <main className="shell not-found"><span className="section-index">404 / НЕ НАЙДЕНО</span><h1>Такого задания пока нет.</h1><p>Возможно, ссылка устарела или задание было архивировано.</p><Link className="button button-primary" href="/challenges">Вернуться к заданиям</Link></main>;
}
