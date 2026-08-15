#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slop_scan.py — детерминированный сканер маркеров нейрослопа (RU + EN).

Что делает:
  1. Ищет словарные маркеры AI-текста по категориям, с контекстом.
  2. Считает метрики ритма: длина предложений, разброс, доля предложений
     из «золотой зоны» 12–20 слов, повторяющиеся начала.
  3. Считает тире, буллет-строки и конструкции «не X, а Y».
  4. Сводит всё в индекс и вердикт.

Это эвристика для редактуры, а НЕ детектор ИИ. Плотность маркеров —
повод перечитать текст, а не доказательство машинного авторства.
Одиночные маркеры встречаются и у живых авторов; диагностично только
сочетание нескольких классов сразу.

Использование:
  python3 slop_scan.py файл.txt
  cat файл.txt | python3 slop_scan.py
  python3 slop_scan.py --exclude-quoted doc.md   # вырезать > цитаты и ```-блоки
                                                   # (для документации о слопе)
"""

import argparse
import re
import sys
from collections import Counter
from statistics import mean, pstdev

# ---------------------------------------------------------------------------
# Словарь маркеров: категория -> список фраз.
# Одно слово трактуется как основа (ловит словоформы: «delv» -> delve/delving).
# Многословные фразы ищутся как цепочка слов с любым пробельным заполнением.
# Источники: Wikipedia «Signs of AI writing», корпусные статьи (Kobak et al.,
# Shapira), СПбГУ, Т—Ж, Хабр, vc.ru, humanizer-ru. См. references/markers-*.md.
# ---------------------------------------------------------------------------

MARKERS = [
    ("RU: вводно-оценочные клише", [
        "важно отметить", "стоит отметить", "следует отметить",
        "важно подчеркнуть", "следует подчеркнуть", "необходимо подчеркнуть",
        "примечательно, что", "безусловно", "несомненно", "как известно",
    ]),
    ("RU: рамки времени и «эпохи»", [
        "в современном мире", "в современном обществе", "в наше время",
        "в наши дни", "в эпоху цифровизации", "в эпоху цифровых технологий",
        "в цифровую эпоху", "в эпоху стремительных",
        "в стремительно меняющемся мире", "на сегодняшний день",
        "с древних времен", "на протяжении всей истории",
    ]),
    ("RU: псевдозначимость", [
        "играет ключевую роль", "играет важную роль", "играет важнейшую роль",
        "занимает особое место", "является неотъемлемой частью",
        "служит свидетельством", "служит напоминанием",
        "оказывает значительное влияние", "вносит неоценимый вклад",
        "неоценимое значение", "краеугольный камень", "культурный код",
        "в днк", "представляет собой", "являет",
    ]),
    ("RU: канцелярит и коннекторы", [
        "таким образом", "следовательно", "кроме того", "более того",
        "в рамках", "в данном контексте", "на данном этапе", "осуществля",
        "широкий спектр", "идет рука об руку", "во-первых", "во-вторых",
        "крайне",
    ]),
    ("RU: промо-лексика", [
        "уникальн", "революционн", "невероятн", "захватывающ",
        "беспрецедентн", "инновационн", "глубокое погружение",
        "открыть для себя", "раскрыть потенциал", "на новый уровень",
        "неповторим", "богатое наследие",
    ]),
    ("RU: ложная интерактивность", [
        "давайте разберемся", "давайте рассмотрим", "давайте погрузимся",
        "знаете ли вы", "представьте себе", "и знаете что",
        "отличный вопрос", "задумывались ли вы",
    ]),
    ("RU: хеджинг и безымянная атрибуция", [
        "эксперты считают", "исследования показывают", "ученые доказали",
        "многие отмечают", "многие считают", "в большинстве случаев",
        "как правило", "может варьироваться", "результаты могут отличаться",
        "не является гарантией", "с одной стороны",
    ]),
    ("RU: синтаксические штампы", [
        "не просто", "дело не в", "будь то", "независимо от того",
        "не только", "подчеркивая важность", "что свидетельствует о",
        "тем самым способствуя", "от новичков до", "от теории до практики",
    ]),
    ("RU: формульные финалы и чат-артефакты", [
        "в заключение", "подводя итог", "в конечном счете", "время покажет",
        "надеюсь, это поможет", "как я уже упоминал",
        "возвращаясь к вашему вопросу",
    ]),

    ("RU: прочистка горла", [
        "дело вот в чем", "горькая правда", "правда в том", "оказывается, что",
        "настоящая проблема", "давайте проясним", "давайте начистоту",
        "давайте поговорим", "интересно вот что", "но есть одна проблема",
        "скажу еще раз", "буду с вами честен",
    ]),
    ("RU: костыли усиления", [
        "и точка", "конец истории", "просто вдумайтесь",
        "это важно потому что", "и вот почему это имеет значение",
        "не поймите меня неправильно",
    ]),
    ("RU: драматические AI-переходы", [
        "и вот тут начинается", "и вот здесь начинается",
        "здесь начинается самое", "тут начинается самое",
        "здесь есть еще один слой", "у этой истории есть второй слой",
        "второй слой", "это подсвечивает", "именно здесь проходит",
        "именно это оказывается ключевым", "самое сильное происходит",
        "самое неприятное", "неудобная правда",
    ]),
    ("RU: риторические подводки", [
        "что если я скажу", "вот что я имею в виду", "подумайте об этом",
        "согласитесь", "послушайте", "смотрите", "и это абсолютно нормально",
    ]),
    ("RU: избыточные притяжательные кальки", [
        "наш продукт", "наша команда", "свои цели", "свою работу", "мой опыт",
    ]),
    ("EN: слова-сигнатуры", [
        "delv", "intricat", "meticulously", "noteworthy", "tapest",
        "testament", "landscape", "realm", "pivotal", "crucial",
        "underscor", "unleash", "harness", "foster", "garner", "boast",
        "vibrant", "multifaceted", "robust", "groundbreaking", "beacon",
        "embark", "showcas", "leverag", "furthermore", "moreover",
    ]),
    ("EN: фразы-клише", [
        "in today's world", "in the digital age", "ever-evolving",
        "fast-paced", "it's important to note", "it's worth noting",
        "in conclusion", "in summary", "at its core",
        "serves as a testament", "plays a crucial role", "plays a vital role",
        "has a profound impact", "whether you're a", "it's not just",
        "let's dive in", "let's dive into", "let's explore",
        "the future looks bright", "only time will tell",
        "experts say", "studies show", "as an ai language model",
        "i hope this helps", "highlighting the importance", "game-changer",
    ]),
]

# ---------------------------------------------------------------------------

WORD_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+(?:[-'’][0-9A-Za-zА-Яа-яЁё]+)*")

NEG_PARALLEL_RU = re.compile(r"\bне\s+[^,.!?;:\n]{1,60}?,\s+а\s+[а-яё]")
NEG_PARALLEL_EN = re.compile(
    r"\bit'?s\s+not\s+[^,.!?;:\n]{1,60}?,\s*it'?s\b"
    r"|\bnot\s+just\s+[^,.!?;:\n]{1,60}?,\s*(?:but|it'?s)\b"
    r"|\bis\s+not\s+about\s+[^,.!?;:\n]{1,60}?,\s*it'?s\s+about\b"
)

BULLET_RE = re.compile(r"^\s*(?:[-*+•▪◦]|\d{1,2}[.)]|[✅🔹🚀💡✔➡])\s+\S")


def normalize(s: str) -> str:
    return s.lower().replace("ё", "е")


def phrase_pattern(phrase: str) -> re.Pattern:
    p = normalize(phrase)
    if " " in p:
        parts = []
        for tok in p.split(" "):
            if tok.endswith(","):
                parts.append(re.escape(tok[:-1]) + r",?")
            else:
                parts.append(re.escape(tok))
        body = r"\s+".join(parts)
        return re.compile(r"(?<!\w)" + body + r"(?!\w)")
    return re.compile(r"(?<!\w)" + re.escape(p) + r"\w*")


PATTERNS = [
    (cat, phrase, phrase_pattern(phrase))
    for cat, phrases in MARKERS
    for phrase in phrases
]


def strip_quoted(text: str) -> str:
    """Убрать blockquote-строки и fenced code-блоки (для документации)."""
    out, in_code = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^\s*>", line):
            continue
        out.append(line)
    return "\n".join(out)


def prose(text: str) -> str:
    """Лёгкая чистка markdown, чтобы разметка не портила метрики."""
    out = []
    for line in text.splitlines():
        line = re.sub(r"^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+•]\s+|\d+[.)]\s+)", "", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        out.append(line)
    return "\n".join(out)


def context(text: str, start: int, end: int, width: int = 170) -> str:
    left = max(text.rfind(c, 0, start) for c in ".!?\n") + 1
    rights = [text.find(c, end) for c in ".!?\n"]
    rights = [r for r in rights if r != -1]
    right = min(rights) + 1 if rights else len(text)
    ctx = re.sub(r"\s+", " ", text[left:right]).strip()
    return ctx if len(ctx) <= width else ctx[: width - 1] + "…"


def scan_markers(text: str, norm: str):
    """Возвращает {категория: {фраза: [контексты]}}."""
    found = {}
    for cat, phrase, pat in PATTERNS:
        for m in pat.finditer(norm):
            found.setdefault(cat, {}).setdefault(phrase, [])
            ctxs = found[cat][phrase]
            if len(ctxs) < 2:
                ctxs.append(context(text, m.start(), m.end()))
    return found


def split_sentences(text: str):
    raw = re.split(r"(?<=[.!?…])[\"'»)\]]*\s+|\n+", text)
    out = []
    for s in raw:
        s = s.strip()
        if WORD_RE.search(s):
            out.append(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Сканер маркеров нейрослопа (RU+EN). Эвристика, не детектор."
    )
    ap.add_argument("path", nargs="?", help="файл с текстом (иначе — stdin)")
    ap.add_argument(
        "--exclude-quoted",
        action="store_true",
        help="пропускать blockquote-строки (>) и fenced code-блоки",
    )
    args = ap.parse_args()

    if args.path:
        try:
            with open(args.path, "r", encoding="utf-8") as f:
                raw = f.read()
        except OSError as e:
            print(f"ошибка чтения {args.path}: {e}", file=sys.stderr)
            return 2
    else:
        raw = sys.stdin.read()

    if args.exclude_quoted:
        raw = strip_quoted(raw)

    text = prose(raw)
    norm = normalize(text)

    words = WORD_RE.findall(norm)
    n_words = len(words)
    if n_words == 0:
        print("пустой ввод: слов не найдено", file=sys.stderr)
        return 2

    sentences = split_sentences(text)
    lengths = [len(WORD_RE.findall(s)) for s in sentences]
    n_sent = len(lengths)

    # --- маркеры ---
    found = scan_markers(text, norm)
    hit_counts = Counter()  # (категория, фраза) -> число вхождений
    for cat, phrase, pat in PATTERNS:
        n = len(pat.findall(norm))
        if n:
            hit_counts[(cat, phrase)] = n
    total_hits = sum(hit_counts.values())
    density = total_hits / n_words * 1000

    # --- ритм ---
    mu = mean(lengths) if lengths else 0.0
    sigma = pstdev(lengths) if len(lengths) > 1 else 0.0
    cv = sigma / mu if mu else 0.0
    golden = sum(1 for ln in lengths if 12 <= ln <= 20)
    golden_share = golden / n_sent if n_sent else 0.0

    openers = Counter()
    for s, ln in zip(sentences, lengths):
        if ln >= 3:
            first = normalize(WORD_RE.findall(s)[0])
            openers[first] += 1
    bad_openers = [(w, c) for w, c in openers.most_common() if c >= 3]

    # --- счётчики ---
    dashes_em = text.count("—")  # длинное тире — типографский маркер
    dashes_en = text.count("–")  # среднее: обычно числовые диапазоны
    dash_per_1000 = dashes_em / n_words * 1000
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    bullets = sum(1 for ln in lines if BULLET_RE.match(ln))
    bullet_share = bullets / len(lines) if lines else 0.0
    neg_ru = list(NEG_PARALLEL_RU.finditer(norm))
    neg_en = list(NEG_PARALLEL_EN.finditer(norm))

    # --- индекс ---
    rhythm_low = n_sent >= 8 and cv < 0.35
    golden_high = n_sent >= 8 and golden_share > 0.60
    dash_high = dashes_em >= 4 and dash_per_1000 > 10
    openers_bad = bool(bad_openers)
    bullets_high = bullets >= 8 and bullet_share >= 0.40
    neg_n = len(neg_ru) + len(neg_en)

    score = density + 0.5 * min(neg_n, 4)
    flags = []
    for name, on in [
        ("ровный ритм (CV<0.35)", rhythm_low),
        (">60% предложений в зоне 12–20 слов", golden_high),
        ("длинные тире >10 на 1000 слов", dash_high),
        ("повторяющиеся начала предложений", openers_bad),
        ("текст — в основном буллеты", bullets_high),
    ]:
        if on:
            score += 1
            flags.append(name)

    if score < 2:
        verdict = "НИЗКАЯ вероятность слопа"
    elif score < 5:
        verdict = "УМЕРЕННАЯ вероятность слопа"
    else:
        verdict = "ВЫСОКАЯ вероятность слопа"

    # --- вывод ---
    src = args.path or "stdin"
    print(f"SLOP SCAN: {src}")
    print(f"Слов: {n_words} | предложений: {n_sent} | непустых строк: {len(lines)}")
    if n_words < 80:
        print("Текст короткий (<80 слов): метрики нестабильны, читайте глазами.")
    print()

    print(f"МАРКЕРЫ: {total_hits} шт., плотность {density:.1f} на 1000 слов")
    if not found:
        print("  словарных маркеров не найдено")
    for cat, _ in MARKERS:
        if cat not in found:
            continue
        cat_hits = sum(hit_counts[(c, ph)] for (c, ph) in hit_counts if c == cat)
        print(f"  [{cat}] — {cat_hits}")
        for phrase, ctxs in found[cat].items():
            print(f"    • «{phrase}» ×{hit_counts[(cat, phrase)]}")
            for ctx in ctxs:
                print(f"        {ctx}")
    print()

    print("РИТМ")
    print(
        f"  длина предложений: средняя {mu:.1f} слов, std {sigma:.1f}, "
        f"min {min(lengths)}, max {max(lengths)}, CV {cv:.2f}"
    )
    print(f"  доля предложений из 12–20 слов: {golden_share * 100:.0f}% ({golden}/{n_sent})")
    if bad_openers:
        lst = ", ".join(f"«{w}» ×{c}" for w, c in bad_openers[:5])
        print(f"  повторяющиеся начала: {lst}")
    else:
        print("  повторяющихся начал (3+) нет")
    print()

    print("СЧЁТЧИКИ")
    print(f"  тире: длинных (—) {dashes_em} шт., {dash_per_1000:.1f} на 1000 слов; "
          f"средних (–) {dashes_en} шт.")
    print(f"  буллет-строки: {bullets} ({bullet_share * 100:.0f}% непустых строк)")
    print(f"  «не X, а Y»-паттерны: RU {len(neg_ru)}, EN {len(neg_en)}")
    for m in neg_ru[:3] + neg_en[:3]:
        print(f"      {context(text, m.start(), m.end())}")
    print()

    print(f"ИНДЕКС СЛОПА: {score:.1f}  (плотность {density:.1f}"
          + (f" + штрафы: {', '.join(flags)}" if flags else ", штрафов нет")
          + (f"; «не X, а Y» ×{neg_n}" if neg_n else "")
          + ")")
    print(f"ВЕРДИКТ: {verdict}")
    print()
    print("Оговорка: эвристика для редактуры, а не детектор ИИ. Плотность")
    print("маркеров — повод перечитать текст по рубрике, а не доказательство")
    print("машинного авторства. Вердикт по одному классу признаков недействителен.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
