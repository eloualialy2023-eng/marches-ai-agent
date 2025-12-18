# -*- coding: utf-8 -*-
import csv
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

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

BASE_URL = "https://www.marchespublics.gov.ma/bdc/entreprise/consultation/"

results = []

def extract_date(text):
    m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%d/%m/%Y").date()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for kw in KEYWORDS:
        print(f"🔎 Recherche: {kw}")
        page.goto(BASE_URL, timeout=60000)

        page.fill("input[type=search]", kw)
        page.keyboard.press("Enter")
        page.wait_for_timeout(4000)

        links = page.locator("a:has-text('Référence')")
        count = links.count()

        for i in range(count):
            href = links.nth(i).get_attribute("href")
            if not href:
                continue

            detail = browser.new_page()
            detail.goto(href, timeout=60000)
            text = detail.inner_text("body")

            date = extract_date(text)
            if date and date > datetime.now().date():
                results.append({
                    "mot_cle": kw,
                    "lien": href,
                    "date_limite": date.strftime("%d/%m/%Y")
                })

            detail.close()

    browser.close()

with open("results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["mot_cle", "lien", "date_limite"])
    writer.writeheader()
    writer.writerows(results)

print("✅ CSV créé:", len(results))
