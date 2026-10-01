# 臺北市長照機構經緯度

5 個 CSV 的「定位用地址」由 GitHub Actions 執行 `geocode.py` 自動轉成經緯度（WGS84）。

- 重新執行：Actions → 產生經緯度 → Run workflow
- 「定位精度」為 `ArcGIS:PointAddress` 表示定位到門牌；`StreetAddress`／`StreetName`／`OSM:*` 精度較低，建議人工檢查。
