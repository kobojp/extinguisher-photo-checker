# 滅火器照片核對

Windows 10／11 桌面程式。選擇年度根目錄及月份，貼上 Excel 欄位或 Markdown 編號表格後按「開始核對」。

## Windows 下載

從 GitHub Releases 下載 Windows ZIP，解壓縮整個資料夾後開啟 `ExtinguisherPhotoChecker.exe`，不需安裝 Python。請保留旁邊的 `_internal` 資料夾。首次使用請選擇自己的年度照片根目錄。

支援清除輸入、紅色數量摘要、複製待補清單及 CSV 匯出。已在 Windows 11 驗證；Windows 10 尚未實機驗證。

## 執行

```powershell
python -m pip install -r requirements.txt
python main.py
```

## 結構

```text
main.py               程式入口
ui.py                 PySide6 桌面介面
checker.py            清單解析、唯讀核對與 CSV 匯出
tests/test_checker.py 核對測試
requirements.txt      執行依賴
assets/app-icon.png   圖示原圖
assets/app-icon.ico   Windows 多尺寸圖示
docs/                 本機核對報告（CSV 不上傳）
```

月份資料夾下可有建築分類，例如 `2026年/8月份更換/中正樓/中-01-122/照片.jpg`。完整編號比對，不會將 `中-01-13` 配到 `中-01-130`；保留數字前導零。照片可放在編號資料夾的子資料夾。相同編號出現在多個位置會合計並提示。

編號同時支援兩段式（`立北-02`、`立南-24`）與三段式（`中-03-148`、`中-B1-127`）。

支援 JPG、JPEG、PNG、HEIC、HEIF、WEBP、BMP、TIF、TIFF。以副檔名及非零檔案大小判定，不會開啟或辨識照片內容，也不保證檔案未損壞或雲端原始檔已下載。未讀取成功會標記「無法讀取」。核對期間請保持磁碟連線；不修改、移動或刪除來源資料。

CSV 使用 UTF-8 BOM，可用 Excel 開啟。設定儲存在目前使用者的 QSettings 中。結果保留上次完成的核對；修改輸入後請再按開始核對。

## 驗證與封裝

```powershell
python -m unittest discover -s tests -v
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --windowed --icon assets/app-icon.ico --add-data "assets/app-icon.ico;assets" --name ExtinguisherPhotoChecker main.py
```

封裝後執行 `dist/ExtinguisherPhotoChecker/ExtinguisherPhotoChecker.exe`，發送時需包含整個資料夾。Windows 10／11 相容性仍應在目標電腦驗證。
