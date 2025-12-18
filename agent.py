# -*- coding: utf-8 -*-
"""
Marches Publics Agent – Version Stable
- استخراج جميع العروض من صفحة القائمة
- فتح صفحات التفاصيل
- فلترة حسب التاريخ (اليوم + المستقبل)
- استخراج المدينة والجهة
- تصدير CSV
"""

import csv
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.marchespublics.gov.ma/bdc/entreprise/consultation/"
BASE_DOMAIN = "https://www.marchespublics.gov.ma"

today = datetime.now().date()
results = []
seen_links = set()

# =============================
# المدن → الجهات
# =============================
CITY_MAP = {
    "RABAT": "Rabat–Salé–Kénitra",
    "SALE": "Rabat–Salé–Kénitra",
    "SALÉ": "Rabat–Salé–Kénitra",
    "KENITRA": "Rabat–Salé–Kénitra",
    "TEMARA": "Rabat–Salé–Kénitra",
    "KHEMISSET": "Rabat–Salé–Kénitra",
    "FES": "Fès–Meknès",
    "MEKNES": "Fès–Meknès",
    "CASABLANCA": "Casablanca–Settat",
    "MOHAMMEDIA": "Casablanca–Settat",
    "SETTAT": "Casablanca–Settat",
}

def get_region_from_city(ville):
    v = (ville or "").upper()
    for city, region in CITY_MAP.items():
        if city in v:
            return region
    return ""

def extract_date_and_city(text):
    m = re.search(r"(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})?", text)
    if not m:
        return None, None

    date_str = m.group(1)
    time_str = m.group(2) or "00:00"

    date_obj = datetime.strptime(
        date_str + " " + time_str,
        "%d/%m/%Y %H:%M"
    )

    ville = ""
    if "Lieu d'exécution" in text:
        part = text.split("Lieu d'exécution", 1)[1]
        lines = [l.strip() for l in part.splitlines() if l.strip()]
        if lines:
            ville = lines[0]

    return date_obj, ville

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print("🔎 تحميل صفحة العروض الرئيسية …")
    page.goto(BASE_URL, timeout=60000)
    page.wait_for_timeout(5000)

    # 🔹 استخراج كل روابط العروض مباشرة
    links = page.locator("a[href*='/bdc/entreprise/consultation/show/']")
    count = links.count()
    print("عدد الروابط في الصفحة:", count)

    for i in range(count):
        href = links.nth(i).get_attribute("href")
        if not href:
            continue

        if href.startswith("/"):
            href = BASE_DOMAIN + href

        if href in seen_links:
            continue
        seen_links.add(href)

        detail = browser.new_page()
        detail.goto(href, timeout=60000)
        body_text = detail.inner_text("body")
        detail.close()

        date_limite, ville = extract_date_and_city(body_text)
        if not date_limite:
            continue

        # فلترة: اليوم + المستقبل
        if date_limite.date() < today:
            continue

        region = get_region_from_city(ville)

        results.append({
            "lien": href,
            "date_limite_date": date_limite.strftime("%d/%m/%Y"),
            "date_limite_time": date_limite.strftime("%H:%M"),
            "ville_execution": ville,
            "region": region
        })

    browser.close()

print("عدد النتائج النهائية:", len(results))

# =============================
# حفظ CSV
# =============================
filename = "marches_filtrees_regions.csv"
with open(filename, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "lien",
        "date_limite_date",
        "date_limite_time",
        "ville_execution",
        "region"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()
    writer.writerows(results)

print("✅ تم إنشاء الملف:", filename)
