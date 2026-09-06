import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from checker import READY, EMPTY, MISSING, ERROR, check_folders, export_csv, parse_codes


class CheckerTests(unittest.TestCase):
    def test_mixed_user_table(self):
        expected = ['中-03-148', '中-04-19', '中-04-58', '中-04-80',
                    '中-05-10', '中-B1-127', '立北-02', '立北-24',
                    '立北-25', '立北-26', '立北-27', '立南-24',
                    '立南-25', '立南-26', '立-10-17', '立南-01',
                    '立南-02', '立北-19', '立北-20']
        expected += [f'立-01-{n:02d}' for n in range(1, 14)]
        table = '\n'.join(f'| {code} |' for code in expected)
        table = table.replace('\n', '\n| -------- |\n', 1)
        codes, invalid, duplicates = parse_codes(table)
        self.assertEqual(invalid, [])
        self.assertEqual(duplicates, [])
        self.assertEqual(codes, expected)
        self.assertEqual(len(codes), 32)

    def test_two_part_exact_folder_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / '立北-02'
            folder.mkdir()
            (folder / 'photo.jpg').write_bytes(b'photo')
            codes, invalid, _ = parse_codes('立北-02\n立北-020\n立南-02')
            self.assertEqual(invalid, [])
            self.assertEqual([r.status for r in check_folders(tmp, codes)],
                             [READY, MISSING, MISSING])

    def test_table_input(self):
        codes, invalid, duplicates = parse_codes('| 編號 |\n| --- |\n| 中-01-13 |\n中-01-13\n中－01－14\n錯誤')
        self.assertEqual(codes, ['中-01-13', '中-01-14'])
        self.assertEqual(duplicates, ['中-01-13'])
        self.assertEqual(invalid, ['錯誤'])

    def test_nested_exact_match_and_empty_photos(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            photo = root / '中正樓' / '中-01-130' / '更換後'
            photo.mkdir(parents=True)
            (photo / 'a.JPG').write_bytes(b'photo')
            empty = root / '中正樓' / '中-01-14'
            empty.mkdir()
            (empty / 'notes.txt').write_text('not a photo')
            (empty / 'empty.jpg').touch()
            result = check_folders(root, ['中-01-130', '中-01-13', '中-01-14'])
            self.assertEqual([r.status for r in result], [READY, MISSING, EMPTY])
            self.assertEqual(result[0].count, 1)
            export_csv(root / 'out.csv', result)
            with (root / 'out.csv').open(encoding='utf-8-sig', newline='') as f:
                self.assertEqual(len(list(csv.reader(f))), 4)

    def test_missing_root_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(check_folders(Path(tmp) / 'missing', ['中-01-1'])[0].status, ERROR)

    def test_basement_codes(self):
        self.assertEqual(parse_codes('中-B2-75\n致-b1-67')[0], ['中-B2-75', '致-B1-67'])

    def test_permission_failure_is_error(self):
        with patch('checker.os.scandir', side_effect=PermissionError('denied')):
            self.assertEqual(check_folders('x', ['中-01-1'])[0].status, ERROR)

    def test_duplicate_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            for building in ['A', 'B']:
                folder = Path(tmp) / building / '中-01-1'
                folder.mkdir(parents=True)
                (folder / 'photo.heic').write_bytes(b'photo')
            r = check_folders(tmp, ['中-01-1'])[0]
            self.assertEqual(r.count, 2)
            self.assertEqual(len(r.paths), 2)


if __name__ == '__main__':
    unittest.main()
