# 把同資料夾內 CSV 的「定位用地址」轉成經緯度（WGS84），寫回「經度」「緯度」欄
# 主要用 ArcGIS World Geocoder（免金鑰）；查不到時改用 OpenStreetMap Nominatim
import csv, glob, re, time, requests

ARC = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
OSM = "https://nominatim.openstreetmap.org/search"
cache = {}

def arcgis(addr):
    r = requests.get(ARC, params={"SingleLine": addr, "f": "json", "maxLocations": 1,
                                  "countryCode": "TWN", "outFields": "Addr_type,Match_addr"}, timeout=30)
    c = r.json().get("candidates", [])
    if not c:
        return None
    a = c[0]["attributes"]
    return (round(c[0]["location"]["x"], 7), round(c[0]["location"]["y"], 7),
            f'ArcGIS:{a.get("Addr_type","")}({c[0]["score"]:.0f})', a.get("Match_addr", ""))

def osm(addr):
    r = requests.get(OSM, params={"q": addr, "format": "json", "limit": 1, "countrycodes": "tw"},
                     headers={"User-Agent": "taipei-care-geocode (github actions)"}, timeout=30)
    j = r.json()
    time.sleep(1.1)
    if not j:
        return None
    return (round(float(j[0]["lon"]), 7), round(float(j[0]["lat"]), 7),
            f'OSM:{j[0].get("type","")}', j[0].get("display_name", ""))

def geocode(addr):
    res = _geocode(addr)
    base = re.sub(r"之\d+號$", "號", addr)
    if base != addr and not res[2].startswith("ArcGIS:PointAddress"):
        res2 = _geocode(base)
        if res2[2].startswith("ArcGIS:PointAddress"):
            return res2[:2] + (res2[2] + "-主門牌",) + res2[3:]
    return res

def _geocode(addr):
    if addr not in cache:
        res = None
        for fn in (arcgis, osm):
            try:
                res = fn(addr)
            except Exception as e:
                print("  錯誤", fn.__name__, e)
            if res:
                break
        cache[addr] = res or ("", "", "查無", "")
        time.sleep(0.3)
    return cache[addr]

for f in sorted(glob.glob("*.csv")):
    rows = list(csv.DictReader(open(f, encoding="utf-8-sig")))
    if not rows or "定位用地址" not in rows[0]:
        continue
    fields = list(rows[0].keys())
    for extra in ("定位精度", "比對結果地址"):
        if extra not in fields:
            fields.append(extra)
    if all(r.get("經度") for r in rows):
        print("已完成，略過：", f)
        continue
    for r in rows:
        if r.get("經度"):
            continue
        x, y, t, m = geocode(r["定位用地址"])
        r["經度"], r["緯度"], r["定位精度"], r["比對結果地址"] = x, y, t, m
        print(r["定位用地址"], x, y, t)
    with open(f, "w", encoding="utf-8-sig", newline="") as o:
        w = csv.DictWriter(o, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("完成：", f)
