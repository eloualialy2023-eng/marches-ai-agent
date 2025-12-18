import csv

data = [
    {"mot_cle": "restauration", "lien": "https://example.com", "date": "30/12/2025"},
    {"mot_cle": "evenement", "lien": "https://example.com", "date": "05/01/2026"},
]

with open("results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

print("CSV created successfully")
