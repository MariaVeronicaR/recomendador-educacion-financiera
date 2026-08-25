"""Reescribe contents.csv con todos los campos entre comillas (csv estándar)."""

import csv

rows = []
with open("/Users/veronica/Desktop/tfm/data/contents.csv", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    for r in reader:
        rows.append(r)

# Asegurar 13 columnas por fila
fixed = []
for r in rows:
    if len(r) < 13:
        r = r + [""] * (13 - len(r))
    if len(r) > 13:
        # probablemente comas internas; intentamos reconstruir
        # Las primeras 12 columnas son las correctas
        r = r[:12] + [",".join(r[12:])]
    fixed.append(r)

with open("/Users/veronica/Desktop/tfm/data/contents.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    writer.writerows(fixed)

print(f"Reescrito con {len(fixed)} filas")
