import contextlib
import io
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from instrumenty.proverit import text_warnings, png_info, main

def chunk(kind, data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(data,zlib.crc32(kind)) & 0xffffffff)

def minimal_png(width=1,height=1):
    header=struct.pack('>IIBBBBB',width,height,8,2,0,0,0)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'IDAT',zlib.compress(b'\0\0\0\0'))+chunk(b'IEND',b'')

class Checks(unittest.TestCase):
    def test_no_claim_of_detection(self):
        self.assertEqual(text_warnings('Готовим дома.\nНормальный текст.'), [])
    def test_words_and_working_note(self):
        result=text_warnings('Есть краш-тест.\n[ПРОВЕРИТЬ]')
        self.assertEqual([x[0] for x in result],[1,2])
    def test_privacy_masks_content(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'text.txt'; p.write_text('Почта test@example.org',encoding='utf8')
            out=io.StringIO()
            with contextlib.redirect_stdout(out): self.assertEqual(main(['text',str(p)]),0)
            self.assertIn('строка 1',out.getvalue()); self.assertNotIn('test@example.org',out.getvalue())
    def test_png_header_and_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'x.png'
            p.write_bytes(minimal_png(1440,1800))
            self.assertEqual(png_info(p)[:2],(1440,1800))
            p.write_bytes(b'broken')
            with self.assertRaises(ValueError): png_info(p)
            data=bytearray(minimal_png());data[20] ^= 1;p.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'контрольная сумма'): png_info(p)
            p.write_bytes(minimal_png()[:-4])
            with self.assertRaises(ValueError): png_info(p)
    def test_duplicate_and_error(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'a.png'; q=Path(temp)/'b.png'
            data=minimal_png(10,20)
            p.write_bytes(data);q.write_bytes(data)
            out=io.StringIO()
            with contextlib.redirect_stdout(out): self.assertEqual(main(['png',str(p),str(q)]),0)
            self.assertIn('Полный дубликат',out.getvalue())
            with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(main(['png',str(Path(temp)/'missing')]),1)
if __name__=='__main__': unittest.main()
