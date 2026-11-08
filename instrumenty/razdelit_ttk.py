#!/usr/bin/env python3
"""Split a specific single-card-per-page PDF, with conservative validation."""
import argparse
import csv
import hashlib
import re
import shutil
import tempfile
from pathlib import Path

import pymupdf

HEADER = re.compile(r'Технологическая\s+карта\s*№\s*(\d+)\s+(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s*Название на чеке:', re.S)
HEAD_COUNT = re.compile(r'Технологическая\s+карта\s*№', re.I)


def safe_name(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip(' .')
    return name[:75].rstrip(' .') or 'Без названия'


def visually_blank(page):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(1, 1), colorspace=pymupdf.csRGB, alpha=False)
    return all(v >= 250 for v in pix.samples)


def split(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(f'Папка уже существует: {output}. Не перезаписываю.')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    doc = pymupdf.open(source)
    if doc.is_encrypted:
        raise ValueError('Документ защищён паролем')
    cards, blanks, seen = [], [], set()
    for i, page in enumerate(doc):
        text = page.get_text()
        m = HEADER.search(text)
        if m and len(HEAD_COUNT.findall(text)) == 1:
            number, date, title = m.group(1), m.group(2), ' '.join(m.group(3).split())
            if number in seen:
                raise ValueError(f'Повтор номера {number} на странице {i+1}: нужна ручная проверка')
            seen.add(number)
            cards.append((i, number, date, title))
        elif not text.strip() and i == len(doc)-1 and visually_blank(page):
            blanks.append(i+1)
        else:
            raise ValueError(f'Неоднозначная страница {i+1}: нужна ручная проверка границ')
    if not cards:
        raise ValueError('Карты не найдены')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.ttk-', dir=output.parent))
    try:
        rows = []
        for i, number, date, title in cards:
            filename = f'{i+1:04d} - №{number} - {safe_name(title)}.pdf'
            part = pymupdf.open()
            part.insert_pdf(doc, from_page=i, to_page=i)
            part.subset_fonts()
            path = staging / filename
            part.save(path, garbage=4, deflate=True)
            part.close()
            # Verify both the extracted content and a rendered comparison with the source.
            with pymupdf.open(path) as check:
                if len(check) != 1 or check[0].get_text() != doc[i].get_text():
                    raise ValueError(f'Текст или количество страниц не совпадают: страница {i+1}')
                mat = pymupdf.Matrix(0.5, 0.5)
                a = doc[i].get_pixmap(matrix=mat, colorspace=pymupdf.csRGB, alpha=False)
                b = check[0].get_pixmap(matrix=mat, colorspace=pymupdf.csRGB, alpha=False)
                if (a.width, a.height, a.n) != (b.width, b.height, b.n):
                    raise ValueError(f'Размер изображения отличается: страница {i+1}')
                # Small rasterizer rounding differences are expected after PDF rewriting.
                if max((abs(x-y) for x, y in zip(a.samples, b.samples)), default=0) > 8:
                    raise ValueError(f'Есть заметные отличия при отрисовке страницы {i+1}')
            rows.append((i+1, number, date, title, filename))
        with (staging / 'index.csv').open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, lineterminator='\n'); writer.writerow(['Страница источника', 'Номер карты', 'Дата', 'Название', 'Файл']); writer.writerows(rows)
        (staging / 'proverka.txt').write_text(
            f'Источник: {source.name}\nSHA-256: {digest}\nСтраниц: {len(doc)}\nКарт: {len(cards)}\n'
            f'Пустая последняя страница не включена: {", ".join(map(str, blanks)) or "нет"}\n'
            'Каждая карта: одна страница; текст и отрисовка сопоставлены с исходной страницей.\n'
            'Исходное содержимое не обезличено. Проверка разбиения не подтверждает правильность рецептов.\n', encoding='utf-8')
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging)
        raise
    finally:
        doc.close()
    return len(cards), blanks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    count, blanks = split(args.source, args.output)
    print(f'Готово: {count} карт; пустые завершающие страницы: {blanks or "нет"}.')
