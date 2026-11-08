#!/usr/bin/env python3
"""Локальные подсказки редактору; не детектор ИИ и не проверка фактов."""
import argparse
import hashlib
import re
import struct
import sys
import zlib
from pathlib import Path

RULES = (
    ('Нежелательное слово: «стафф»', re.compile(r'(?iu)(?<!\w)стафф(?!\w)')),
    ('Нежелательное слово: «мишура»', re.compile(r'(?iu)(?<!\w)мишур[аыоеу](?!\w)')),
    ('Нежелательное слово: «краш-тест»', re.compile(r'(?iu)(?<!\w)краш[\s-]тест(?!\w)')),
    ('Возможно, шаблонный оборот: проверьте смысл', re.compile(r'(?iu)\b(?:в современном мире|важно отметить|это не просто)\b')),
    ('Рабочая пометка: проверьте перед публикацией', re.compile(r'(?iu)\[(?:проверить|черновик|уточнить)\]')),
    ('Возможно, адрес электронной почты: проверьте анонимность', re.compile(r'(?iu)\b[\w.+-]+@[\w.-]+\.[a-zа-я]{2,}\b')),
    ('Возможно, телефон: проверьте анонимность', re.compile(r'(?<!\d)(?:\+?7|8)[\s()\-]*\d{3}[\s()\-]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}(?!\d)')),
)

def text_warnings(content):
    result=[]
    for number,line in enumerate(content.splitlines(),1):
        for label,pattern in RULES:
            if pattern.search(line): result.append((number,label))
    return result

def png_info(path):
    """Stream PNG chunks and verify CRCs; this does not decode pixels."""
    with path.open('rb') as f:
        if f.read(8) != b'\x89PNG\r\n\x1a\n':
            raise ValueError('неверная сигнатура PNG')
        width = height = None
        saw_data = False
        index = 0
        while True:
            header = f.read(8)
            if len(header) != 8:
                raise ValueError('повреждён или оборван блок PNG')
            length, kind = struct.unpack('>I4s', header)
            if index == 0 and (kind != b'IHDR' or length != 13):
                raise ValueError('отсутствует корректный IHDR')
            if kind == b'IHDR' and index != 0:
                raise ValueError('повторный IHDR')
            if kind == b'IEND' and length != 0:
                raise ValueError('неверный IEND')
            crc = zlib.crc32(kind)
            remaining = length
            first = b''
            while remaining:
                data = f.read(min(remaining, 1024 * 1024))
                if not data:
                    raise ValueError('оборваны данные PNG')
                if kind == b'IHDR': first += data
                crc = zlib.crc32(data, crc)
                remaining -= len(data)
            checksum = f.read(4)
            if len(checksum) != 4 or struct.unpack('>I', checksum)[0] != crc & 0xffffffff:
                raise ValueError('неверная контрольная сумма PNG')
            if kind == b'IHDR':
                width, height = struct.unpack('>II', first[:8])
                if not width or not height:
                    raise ValueError('нулевой размер PNG')
            if kind == b'IDAT': saw_data = True
            if kind == b'IEND':
                if not saw_data: raise ValueError('отсутствует IDAT')
                if f.read(1): raise ValueError('лишние данные после IEND')
                break
            index += 1
    return width, height, path.stat().st_size

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for command,helptext in [('text','подсказки по тексту'),('png','размеры PNG и повторные файлы')]:
        p=sub.add_parser(command,help=helptext)
        p.add_argument('files',nargs='+',type=Path)
    args=parser.parse_args(argv)
    failures=0; seen={}
    for path in args.files:
        try:
            if args.command=='text':
                content=path.read_text(encoding='utf-8')
                warnings=text_warnings(content)
                print(f'{path}: строк {len(content.splitlines())}, знаков {len(content)}; подсказок {len(warnings)}')
                for number,label in warnings: print(f'  строка {number}: {label}')
                print('  Ручная проверка смысла, фактов и анонимности обязательна.')
            else:
                w,h,size=png_info(path)
                with path.open('rb') as f:
                    digest=hashlib.file_digest(f,'sha256').hexdigest()
                print(f'{path}: {w}×{h}, {size} байт; SHA-256 {digest[:12]}')
                if digest in seen: print(f'  Полный дубликат: {seen[digest]}')
                else: seen[digest]=path
                print('  Проверены блоки и CRC, но не декодирование пикселей; визуал и отображение в VK проверяются вручную.')
        except (OSError,UnicodeError,ValueError) as exc:
            failures+=1; print(f'{path}: ошибка чтения: {exc}',file=sys.stderr)
    return 1 if failures else 0
if __name__=='__main__': raise SystemExit(main())
