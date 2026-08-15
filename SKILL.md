---
name: "антислоп"
description: "Integrate new slop markers into scanner"
---

# Интеграция новых маркеров в slop_scan.py

Заменить `scripts/slop_scan.py` версией, где новые классы из `slop-stop` встроены в основной список `MARKERS`. Это делает сканер сразу действующим без ручного импорта `slop_scan_additions.py`.
