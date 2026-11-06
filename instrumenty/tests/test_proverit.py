import contextlib
import io
import struct
import tempfile
import unittest
from pathlib import Path
from instrumenty.proverit import text_warnings, png_info, main

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
            p.write_bytes(b'\x89PNG\r\n\x1a\n'+b'\0\0\0\rIHDR'+struct.pack('>II',1440,1800))
            self.assertEqual(png_info(p)[:2],(1440,1800))
            p.write_bytes(b'broken')
            with self.assertRaises(ValueError): png_info(p)
    def test_duplicate_and_error(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'a.png'; q=Path(temp)/'b.png'
            data=b'\x89PNG\r\n\x1a\n'+b'\0\0\0\rIHDR'+struct.pack('>II',10,20)
            p.write_bytes(data);q.write_bytes(data)
            out=io.StringIO()
            with contextlib.redirect_stdout(out): self.assertEqual(main(['png',str(p),str(q)]),0)
            self.assertIn('Полный дубликат',out.getvalue())
            with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(main(['png',str(Path(temp)/'missing')]),1)
if __name__=='__main__': unittest.main()
