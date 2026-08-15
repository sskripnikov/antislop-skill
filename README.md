# Антислоп

Навык для аудита, переписывания и превентивной генерации русского текста без
нейрослопа: клише, RLHF-голоса, драматических AI-переходов, риторических
подводок, канцелярита, метрономного ритма и фальшивой хуманизации.

## Что внутри

- `SKILL.md` — рабочая инструкция навыка.
- `references/markers-ru.md` — словарь русских маркеров.
- `references/markers-en.md` — английские маркеры для смешанных текстов.
- `references/rewrite-playbook.md` — тактики точечной правки.
- `references/scoring-rubric.md` — рубрика 5 осей и anti-overcorrection.
- `references/detectors-brief.md` — почему AI-детекторы не должны быть целью.
- `assets/prompt-templates.md` — шаблоны для аудита, рерайта и self-critique.
- `scripts/slop_scan.py` — детерминированный сканер маркеров RU/EN.

## Быстрый запуск сканера

```bash
python3 scripts/slop_scan.py text.txt
cat text.txt | python3 scripts/slop_scan.py
python3 scripts/slop_scan.py --exclude-quoted doc.md
```

Сканер — редакторская эвристика, не детектор ИИ. Его вердикт показывает,
где перечитать текст глазами, а не доказывает машинное авторство.

## Источники и доноры

Навык собран вокруг русскоязычной редакторской практики и дополнен
структурными маркерами из `skosovsky/slop-stop`.
