"""Read-only folder checks, independent of the desktop UI."""
import csv
import os
import re
from dataclasses import dataclass
from pathlib import Path

PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.bmp', '.tif', '.tiff'}
CODE = re.compile(r'^[\u3400-\u9fffA-Za-z]+-(?:[A-Z]*\d+-)?\d+$')
READY, EMPTY, MISSING, ERROR = '已有照片', '資料夾無照片', '未找到資料夾', '無法讀取'


def normalize(value):
    return value.strip().replace('－', '-').replace('–', '-').replace('—', '-').upper()


def parse_codes(text):
    codes, invalid, duplicates = [], [], []
    for line in text.splitlines():
        for cell in re.split(r'[|\t,，]', line):
            code = normalize(cell)
            if not code or re.fullmatch(r':?-+:?', code) or code in {'編號', '核對編號'}:
                continue
            if not CODE.fullmatch(code):
                invalid.append(cell.strip())
            elif code in codes:
                duplicates.append(code)
            else:
                codes.append(code)
    return codes, invalid, duplicates


@dataclass
class Result:
    code: str
    status: str
    count: int | None
    paths: list[str]
    detail: str = ''


def check_folders(month_path, codes):
    root = Path(month_path)
    index, scan_errors = {}, []
    # scandir raises on inaccessible/missing roots instead of silently treating them as empty.
    try:
        with os.scandir(root):
            pass
    except OSError as exc:
        return [Result(c, ERROR, None, [], str(exc)) for c in codes]
    for parent, dirs, _ in os.walk(root, onerror=lambda e: scan_errors.append(str(e))):
        for name in dirs:
            key = normalize(name)
            if key in codes:
                index.setdefault(key, []).append(str(Path(parent) / name))
    results = []
    for code in codes:
        paths = index.get(code, [])
        if not paths:
            results.append(Result(code, ERROR if scan_errors else MISSING, None, [], '\n'.join(scan_errors)))
            continue
        errors, count = [], 0
        for folder in paths:
            try:
                with os.scandir(folder):
                    pass
            except OSError as exc:
                errors.append(str(exc))
                continue
            for parent, _, files in os.walk(folder, onerror=lambda e: errors.append(str(e))):
                for name in files:
                    if Path(name).suffix.lower() in PHOTO_EXTENSIONS:
                        try:
                            if (Path(parent) / name).stat().st_size > 0:
                                count += 1
                        except OSError as exc:
                            errors.append(str(exc))
        detail = '\n'.join(errors)
        if len(paths) > 1:
            detail = f'找到 {len(paths)} 個同編號資料夾，照片數為合計。\n' + detail
        results.append(Result(code, ERROR if errors else READY if count else EMPTY,
                              None if errors else count, paths, detail.strip()))
    return results


def export_csv(path, results):
    with open(path, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['編號', '狀態', '照片數', '資料夾', '說明'])
        for r in results:
            writer.writerow([r.code, r.status, r.count if r.count is not None else '', '\n'.join(r.paths), r.detail])
