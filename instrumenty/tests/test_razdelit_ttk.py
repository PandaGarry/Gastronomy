import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    import pymupdf
    from instrumenty.razdelit_ttk import split, safe_name
except ImportError:
    pymupdf = None


@unittest.skipIf(pymupdf is None, 'Для теста нужен PyMuPDF')
class SplitTests(unittest.TestCase):
    def make_source(self, root, values, blank=False):
        path = root / 'source.pdf'
        doc = pymupdf.open()
        for value in values:
            page = doc.new_page()
            page.insert_text((50, 50), value)
        if blank:
            doc.new_page()
        doc.save(path); doc.close()
        return path

    def test_names_sanitised(self):
        self.assertEqual(safe_name(' bad:/name? '), 'bad name')

    def test_split_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = self.make_source(root, ['original'], blank=True)
            # Synthetic test PDF uses ASCII text; substitute only metadata detection.
            with mock.patch('instrumenty.razdelit_ttk.HEADER') as header, mock.patch('instrumenty.razdelit_ttk.HEAD_COUNT') as count:
                header.search.side_effect = lambda text: mock.Mock(group=lambda n: {1:'001', 2:'01.01.2024', 3:'Card'}[n]) if text.strip() else None
                count.findall.return_value = ['head']
                self.assertEqual(split(source, root/'out'), (1, [2]))
                self.assertEqual(len(list((root/'out').glob('*.pdf'))), 1)
                with self.assertRaises(FileExistsError):
                    split(source, root/'out')

    def test_ambiguous_page_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = self.make_source(root, ['unknown'])
            with self.assertRaisesRegex(ValueError, 'Неоднозначная страница'):
                split(source, root/'out')
            self.assertFalse((root/'out').exists())

if __name__ == '__main__':
    unittest.main()
