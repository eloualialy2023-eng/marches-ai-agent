# -*- coding: utf-8 -*-
"""
AI Agent – marchespublics.gov.ma
- البحث بالكلمات المفتاحية
- استخراج العروض المستقبلية فقط
- استخراج المدينة
- توحيد الجهة
- تصدير CSV
"""

import csv
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# =============================
# الكلمات المفتاحية
# =============================
KEYWORDS = [
    "restauration",
    "evenement ciel",
    "Gestion d’evenements",
    "Installation de tentes",
    "Organisation",
    "Organisation evenement",
    "pause cafe",
    "buffet",
    "dejeuner",
    "boissons",
    "lunch box",
    "repas",
    "chapiteau",
    "reception"
]

# =============================
# المدن → الجهات
# =============================
CITY_MAP = {
    # Rabat–Salé–Kénitra
    "RABAT": "Rabat–Salé–Kénitra",
    "SALE": "Rabat–Salé–Kénitra",
    "SALÉ": "Rabat–Salé–Kénitra",
    "KENITRA": "Rabat–Salé–Kénitra",
    "KÉNITRA": "Rabat–Salé–Kénitra",
    "TEMARA": "Rabat–Salé–Kénitra",
    "TÉMARA": "Rabat–Salé–Kénitra",
    "KHEMISSET": "Rabat–Salé–Kénitra",
    "KHÉMISSET": "Rabat–Salé–Kénitra",

    # Fès–Meknès
    "FES": "Fès–Meknès",
    "FÈS": "Fès–Meknès",
    "MEKNES": "Fès–Meknès",
    "MEKNÈS": "Fès–Meknès",

    # Casablanca–Settat
    "MOHAMMEDIA": "Casablanca–Settat",
    "SETTAT": "Casablanca–Settat",
    "KHOURIBGA": "Casablanca–Settat",
}

def get_region_from_city(ville):
    v = (ville or "").upper()
    for city, region in CITY_MAP.items():
        if city in v:
            return region
    return ""

# =============================
# الإعدادات
# =============================
BASE_URL = "https://www.marchespublics.gov.ma/bdc/entreprise/consultation/"
BASE_DOMAIN = "https://www.marchespublics.gov.ma"

results = []
seen_links = set()
today = datetime.now().date()

# =============================
# أدوات استخراج
# =============================
def extract_date_and_city(text):
    # التاريخ
    m = re.search(r"(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})?", text)
    if not m:
        return None, None

    date_str = m.group(1)
    time_str = m.group(2) or "00:00"
    date_obj = datetime.strptime(
        date_str + " " + time_str,
        "%d/%m/%Y %H:%M"
    )

    # المدينة
    ville = ""
    if "Lieu d'exécution" in text:
        part = text.split("Lieu d'exécution", 1)[1]
        lines = [l.strip() for l in part.splitlines() if l.strip()]
        if lines:
            ville = lines[0]

    return date_obj, ville

# =============================
# التنفيذ
# =============================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for kw in KEYWORDS:
        print(f"🔎 Recherche: {kw}")

        page.goto(BASE_URL, timeout=60000)

        # انتظار خانة إدخال
        page.wait_for_selector("input", timeout=60000)
        search_input = page.locator("input").first
        search_input.fill(kw)
        search_input.press("Enter")

        page.wait_for_timeout(4000)

        links = page.locator("a:has-text('Référence')")
        count = links.count()

        for i in range(count):
            href = links.nth(i).get_attribute("href")
            if not href:
                continue

            # إكمال الرابط إن كان ناقصًا
            if href.startswith("/"):
                href = BASE_DOMAIN + href

            if href in seen_links:
                continue
            seen_links.add(href)

            detail = browser.new_page()
            detail.goto(href, timeout=60000)
            body_text = detail.inner_text("body")

            date_limite, ville = extract_date_and_city(body_text)
            detail.close()

            if not date_limite:
                continue

            

            region = get_region_from_city(ville)

            results.append({
                "mot_cle": kw,
                "lien": href,
                "date_limite_date": date_limite.strftime("%d/%m/%Y"),
                "date_limite_time": date_limite.strftime("%H:%M"),
                "ville_execution": ville,
                "region": region
            })

    browser.close()

# =============================
# حفظ CSV
# =============================
filename = "marches_filtrees_regions.csv"
with open(filename, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "mot_cle",
        "lien",
        "date_limite_date",
        "date_limite_time",
        "ville_execution",
        "region"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()
    writer.writerows(results)

print("✅ انتهى التنفيذ")
print(f"📄 عدد العروض: {len(results)}")
print(f"📁 الملف: {filename}")

