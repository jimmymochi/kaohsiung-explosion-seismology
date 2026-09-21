# 臺灣重大工業氣爆地震學觀測與分析專題

本專案整合臺灣近十年三大重大工業氣爆事件（**2014 年高雄地下箱涵丙烯氣爆**、**2019 年雲林麥寮台化芳香烴氣爆**、**2023 年屏東明揚科技大爆炸**）之連續地震波記錄，以地球物理與法醫地震學（Forensic Seismology）方法，重現京都大學防災研究所 Masumi Yamada 等人（2014）之成果，並全面將繪圖技術升級至 **GMT (Generic Mapping Tools 6.5.0)** 專業出版標準。

---

## 專案亮點與核心成果

1. **繪圖引擎全面升級至 GMT 6.5.0 Modern Mode**：
   - 解決過去純 Python (Matplotlib) 在大動態範圍、大地測量橢球投影、SAC 地震學剖面倒置軸（Record Section）與微刻度渲染之侷限。
   - 產出 9 幅國際期刊級高解析度地震圖表（GMT 01 至 GMT 09），包括全臺事件分佈圖、同心等震距環、近場六分量矩陣、帶通濾波對比與 STFT 時頻譜。
2. **三大氣爆事件地震學深度剖析**：
   - **2014 高雄氣爆**：揭示固體地殼波（$v \approx 3.5\text{ km/s}$）與大氣超壓音爆波（$v \approx 0.34\text{ km/s}$）在近場與遠場的到時分離與「空地耦合波 (Air-to-ground coupled waves)」效應。
   - **2019 雲林麥寮氣爆**：露天設備破裂造成地下岩層固體耦合極微弱，但於 39.9 km 外的 CHY 測站記錄到在 112.7 秒到達之極強垂直空氣震波。
   - **2023 屏東明揚大爆炸**：雙測站六分量波形與時頻分析確認相隔 109 秒的「雙波爆轟機制」，第二次爆轟振幅高達第一次的 2.5~3 倍，客觀印證化學過氧化物二次殉爆。
3. **一頁式互動展示網頁 (`index.html`)**：
   - 整合現代深色地球物理儀表板風格。
   - **Python vs GMT vs 論文原圖 8 大主題互動切換對比器**。
   - **地震訊號音訊化試聽 (Web Audio Seismic Sonification)**：將次聲波頻段時間壓縮加速，用耳朵身歷其境「聽見」氣爆地動與音爆。
   - 測站結構化資料庫表格與一鍵 JSON 匯出。

---

## 成果檔案目錄架構

```
D:\JIMMY CHEN\達意專題\高雄氣爆\
├── index.html                                 # GitHub Pages 網站首頁（直接發布）
├── README.md                                  # 專案中文說明文件
├── 生成氣爆地震圖表與分析.py                   # Python與GMT一鍵全自動產出腳本
├── 建立網頁.py                                 # 網頁靜態產生器
├── 驗證連結.py                                 # 圖片連結完整性校驗腳本
├── 2014event-從地震儀的視角看...masumi.pdf       # 原始文獻投影片參考檔案
│
├── GMT繪圖成果/                                # GMT 6.5 現代模式產出高階向量圖
│   ├── GMT_01_高雄氣爆_震波距離剖面圖.png
│   ├── GMT_02_高雄氣爆_原始與帶通濾波對比圖.png
│   ├── GMT_03_高雄氣爆_近場三分量時序圖.png
│   ├── GMT_04_高雄氣爆_核心測站時頻譜圖.png
│   ├── GMT_05_臺灣南部測站與氣爆震央分佈地圖.png
│   ├── GMT_06_2019雲林麥寮氣爆_三分量波形與時頻圖.png
│   ├── GMT_07_2023屏東明揚大爆炸_雙測站六分量波形圖.png
│   ├── GMT_08_2023屏東明揚大爆炸_時頻譜與雙波能量分析.png
│   └── GMT_09_臺灣三大重大工業氣爆事件分佈圖.png
│
├── Python繪圖成果/                             # Python (Matplotlib + ObsPy) 對照圖檔
│   ├── PY_01_高雄氣爆_震波距離剖面圖.png
│   ├── PY_02_高雄氣爆_原始與帶通濾波對比圖.png
│   ├── PY_03_高雄氣爆_近場三分量時序圖.png
│   ├── PY_04_高雄氣爆_核心測站時頻譜圖.png
│   ├── PY_06_2019雲林麥寮氣爆_三分量波形與時頻圖.png
│   ├── PY_07_2023屏東明揚大爆炸_雙測站六分量波形圖.png
│   └── PY_08_2023屏東明揚大爆炸_時頻譜與雙波能量分析.png
│
├── PDF參考圖/                                  # 原始研究論文簡報各頁高清圖
├── 原始資料/                                   # MiniSEED 原始連續地震觀測資料
└── 網頁成果/                                   # 結構化資料庫與中繼備份
    ├── 氣爆地震資料庫.json
    └── index.html
```

---

## 3 步驟發布至 GitHub Pages

### 步驟 1：在資料夾初始化 Git 倉庫並提交
開啟 PowerShell，切換至本資料夾：
```powershell
cd "D:\JIMMY CHEN\達意專題\高雄氣爆"
git init
git add .
git commit -m "feat: 臺灣三大重大工業氣爆地震學分析與GMT展示網頁"
```

### 步驟 2：建立 GitHub 倉庫並推播 (以 GitHub CLI 為例)
```powershell
gh repo create kaohsiung-explosion-seismology --public --source=. --remote=origin --push
```
*或手動在 GitHub 建立倉庫後執行：*
```powershell
git remote add origin https://github.com/您的帳號/kaohsiung-explosion-seismology.git
git branch -M main
git push -u origin main
```

### 步驟 3：在 GitHub 啟用 GitHub Pages
1. 前往 GitHub 倉庫 -> **Settings** -> 左側選單點擊 **Pages**。
2. 在 **Build and deployment** 下方的 **Source** 選擇 `Deploy from a branch`。
3. **Branch** 選擇 `main`，資料夾選擇 `/(root)`，點擊 **Save**。
4. 約等待 1 分鐘後，即可在頁面頂端取得全域公開網址：
   `https://您的帳號.github.io/kaohsiung-explosion-seismology/`
