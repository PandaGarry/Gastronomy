"use client";

import { useState, type FormEvent } from "react";
import { CheckCircle2, ImagePlus, Send, X } from "lucide-react";

export function SubmissionComposer({ challengeTitle }: { challengeTitle: string }) {
  const [files, setFiles] = useState<File[]>([]);
  const [note, setNote] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  function handleFiles(selected: FileList | null) {
    if (!selected) return;
    const next = Array.from(selected);
    const invalid = next.find((file) => !file.type.startsWith("image/"));
    if (invalid) {
      setError("Можно добавить только изображения.");
      return;
    }
    if (next.length + files.length > 3) {
      setError("Для демо-публикации можно выбрать не более трёх фотографий.");
      return;
    }
    setError("");
    setFiles((current) => [...current, ...next]);
  }

  function removeFile(index: number) {
    setFiles((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (files.length === 0) {
      setError("Добавьте хотя бы одну фотографию результата.");
      return;
    }
    setError("");
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <section className="submission-success" aria-live="polite">
        <CheckCircle2 size={34} />
        <h2>Черновой сценарий пройден!</h2>
        <p>В реальном продукте публикация отправилась бы на модерацию. Сейчас данные остаются только в этой демонстрации и никуда не загружаются.</p>
        <button className="button button-quiet" type="button" onClick={() => setSubmitted(false)}>Вернуться к публикации</button>
      </section>
    );
  }

  return (
    <form className="submission-form" onSubmit={handleSubmit}>
      <div className="form-field">
        <label htmlFor="submission-photos">Фотографии результата <span>Обязательно · до 3 фото</span></label>
        <label className="upload-zone" htmlFor="submission-photos">
          <ImagePlus size={25} />
          <strong>Выберите фотографии</strong>
          <small>JPG, PNG или WebP · локальный демо-выбор</small>
        </label>
        <input id="submission-photos" className="visually-hidden" type="file" accept="image/*" multiple onChange={(event) => handleFiles(event.target.files)} />
        {files.length > 0 && <ul className="selected-files">{files.map((file, index) => <li key={`${file.name}-${index}`}><span>{file.name}</span><button type="button" onClick={() => removeFile(index)} aria-label={`Удалить ${file.name}`}><X size={15} /></button></li>)}</ul>}
      </div>
      <div className="form-field">
        <label htmlFor="submission-note">Небольшая история <span>Необязательно · до 500 символов</span></label>
        <textarea id="submission-note" value={note} maxLength={500} onChange={(event) => setNote(event.target.value)} placeholder="Что получилось особенно хорошо? Что попробовали впервые?" rows={4} />
        <small className="character-count">{note.length}/500</small>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button button-primary submit-button" type="submit"><Send size={16} /> Отправить результат</button>
      <p className="form-disclaimer">Это UX-демо: файлы не загружаются на сервер, публикация не создаётся и XP не начисляются.</p>
    </form>
  );
}
