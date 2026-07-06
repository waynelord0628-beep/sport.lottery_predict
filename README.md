# 私用運彩預測儀表板

這是一個本機私用版，不含登入、解鎖、付費。核心流程是：

1. 執行 `update_predictions.bat` 下載 Football-Data 歷史足球比分與賠率。
2. 在 `data/upcoming_matches.csv` 放接下來要預測的比賽與賠率，可以混足球、棒球、電競。
3. 批次檔會自動產生 `dashboard_data.js`。
4. 打開 `index.html` 查看預測、單場細節與回測。

## 模型邏輯

- 從 Football-Data 抓五大聯賽歷史賽果與賠率。
- 優先使用 closing odds；沒有 closing odds 才退回 pre-closing odds。
- 用歷史賽果逐場更新隊伍 Elo。
- 用 Elo 機率與市場隱含機率做校準混合。
- 用 Poisson 分佈估預期進球、比分、大 2.5 與 BTTS。
- 用 `EV = 模型機率 * 賠率 - 1` 判斷價值單。
- 回測用時間切分與逐場更新，避免偷看未來結果。
- 報告輸出在 `reports/data_quality.json` 和 `reports/model_report.json`。

## 棒球與電競

`data/upcoming_matches.csv` 支援 `sport` 欄位：

```csv
id,sport,league,kickoff,home,away,odds_home,odds_draw,odds_away,odds_over25,odds_btts
m1,soccer,Premier League,手動更新,Arsenal,Chelsea,1.82,3.75,4.40,1.86,1.74
m2,baseball,MLB,手動更新,New York Yankees,Boston Red Sox,1.78,,2.08,,
m3,esports,LoL,手動更新,T1,Gen.G,1.92,,1.88,,
```

棒球和大多數電競是二選一盤口，所以 `odds_draw` 留空。

如果你有 The Odds API key，可以在 Windows 設定：

```bat
set THE_ODDS_API_KEY=你的APIKEY
```

然後執行 `update_predictions.bat`。它會嘗試抓：

- MLB：`baseball_mlb`
- LoL：`esports_lol`
- CS2：`esports_cs2`
- Dota 2：`esports_dota2`

沒有 API key 時，系統會保留手動的 `upcoming_matches.csv`。

## CSV 欄位

`historical_matches.csv`

```csv
date,league,home,away,home_score,away_score,odds_home,odds_draw,odds_away,odds_over25,odds_btts
```

`upcoming_matches.csv`

```csv
id,league,kickoff,home,away,odds_home,odds_draw,odds_away,odds_over25,odds_btts
```

## 想提高準確度

最重要的是資料品質和持續回測，不是調 UI：

- 每隊至少 30 到 100 場近期資料。
- 賠率要存「預測當下」的賠率，不要用賽後更新過的收盤價混在一起。
- 分聯賽校準，不同聯賽平均進球和主場優勢不同。
- 每週看 backtest，調整主場優勢、Elo K 值、信心門檻與 EV 門檻。

目前自動資料源的限制：

- Football-Data 適合做足球歷史回測與校準。
- 棒球、電競目前先支援 upcoming odds 與二選一模型；要做真正回測，需要再接 MLB/電競歷史賽果與歷史賠率。
- 真正賽前即時賠率通常需要 Odds API / bookmaker API key。
- 沒有 API key 時，請手動更新 `data/upcoming_matches.csv`。
