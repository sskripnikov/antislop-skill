#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slop_scan.py — детерминированный сканер маркеров нейрослопа (RU + EN).

Что делает:
  1. Ищет словарные маркеры AI-текста по категориям, с контекстом.
  2. Считает метрики ритма: длина предложений, разброс, доля предложений
     из «золотой зоны» 12–20 слов, доля рубленых фраз (≤3 слов),
     повторяющиеся начала.
  3. Считает тире, многоточия, буллет-строки, конструкции «не X, а Y»,
     абсолюты и притяжательные местоимения (кальки с английского).
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
    ("RU: мета-комментарии и анонсы", [
        "дело вот в чем", "правда в том, что", "горькая правда",
        "реальность такова", "настоящая проблема в том",
        "давайте проясним", "давайте начистоту", "когда дело доходит до",
        "но это уже тема для другого", "это не баг, а фича",
        "буду с вами честен", "не поймите меня неправильно",
        "просто вдумайтесь", "конец истории", "поверьте мне",
        "вы и так это знаете", "забегая вперед", "обещаю вам",
    ]),
    ("RU: корпоративные кальки", [
        "ландшафт", "геймчейнджер", "меняет правила игры", "дипдайв",
        "распаков", "лавирова", "выйти из зоны комфорта",
        "сделать шаг назад", "двигаясь вперед", "удвоить усилия",
        "на одной волне", "бесшовн", "в конце дня", "адресовать проблему",
        "драйвить", "синкануться",
    ]),
    # Однозначные обороты обороны от невысказанного возражения и отклонения
    # фальшивой альтернативы (markers-ru.md §9.9–9.10). Двусмысленные
    # («казалось бы», «судя по всему») в индекс не идут: они частотны
    # у живых авторов, для них ниже отдельный справочный счётчик.
    ("RU: черновиковые следы", [
        "речь не о том", "я не утверждаю", "мы не утверждаем",
        "можно возразить", "кто-то скажет", "можно было бы пойти",
        "очевидное решение", "не поймите неправильно",
    ]),
    ("RU: дежурные «вызовы и перспективы»", [
        "несмотря на существующие вызовы", "несмотря на вызовы",
        "несмотря на все вызовы", "несмотря на трудности",
        "вместе с тем сохраняется", "перспективы развития",
        "имеет все шансы", "продолжает динамично развиваться",
        "при сохранении текущих темпов", "сохраняет значительный потенциал",
        "в долгосрочной перспективе",
    ]),
    ("RU: догадка вместо пробела", [
        "предпочитает не афишировать", "не афишир", "закрытость информации",
        "традиционно для отрасли",
    ]),
    ("RU: name-dropping", [
        "постоянный эксперт", "регулярно выступает", "тысяч подписчиков",
        "ведущих деловых изданий", "федеральных телеканал",
    ]),
    ("RU: формульные финалы и чат-артефакты", [
        "в заключение", "подводя итог", "в конечном счете", "время покажет",
        "надеюсь, это поможет", "как я уже упоминал",
        "возвращаясь к вашему вопросу",
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

ELLIPSIS_RE = re.compile(r"…|\.\.\.")

# Абсолюты как ложная авторитетность (markers-ru.md §8.9). Голое «все»
# в список не берём: слишком частотно у живых авторов.
ABSOLUTE_RE = re.compile(
    r"(?<!\w)(?:всегда|никогда|никто|ничто|ничего подобного"
    r"|кажд(?:ый|ая|ое|ые|ого|ой|ому|ым|ыми|ых)"
    r"|ни один|ни одна|ни одного|ни одной"
    r"|без исключени\w*|абсолютно все\w*|на 100%|стопроцентн\w*)(?!\w)"
)

# Афоризм-формулы (markers-ru.md §8.10): готовая формула глубокомыслия
# вместо утверждения. Счётчик справочный и в индекс не идёт: «русский —
# это язык межнационального общения» под шаблон тоже попадает, а маркером
# не является. Решает человек, для того и печатается контекст.
APHORISM_RE = re.compile(
    r"(?:—|--)\s*(?:это\s+)?"
    r"(?:язык|валюта|архитектура|зеркало|днк|топливо|религия|новая нефть)"
    r"\s+[а-яё]{4,}"
    r"|станов(?:ит|ят)ся\s+ловушкой"
    r"|(?<!\w)не\s+инструмент,?\s+а\s+зеркало"
)

# Двусмысленные обороты догадки и черновикового следа (markers-ru.md §7.1,
# §9.9–9.10): «казалось бы», «судя по всему», «вероятно». Счётчик справочный
# и в индекс не идёт — у живых авторов это нормальная риторика. Маркером они
# становятся в связке: признание пробела плюс догадка, отвергнутый вариант,
# который больше нигде не всплывает. Решает человек, для того и контекст.
SPECULATION_RE = re.compile(
    r"(?<!\w)(?:казалось бы|соблазнительно|по всей видимости|судя по всему"
    r"|можно предположить|вероятно|как можно предположить"
    r"|это не значит,? что|не раскрыва(?:ет|ют)ся|не разглаша(?:ет|ют)ся)"
    r"(?!\w)"
)

# Пассив с пропавшим субъектом (markers-ru.md §8.12): «было принято решение»,
# «отмечается рост», «рекомендуется усилить». Три ветки: связка «был + краткое
# страдательное причастие», безличные возвратные глаголы и голое краткое
# причастие канцелярского обихода. Счётчик с оговоркой: в приказе, протоколе
# и регламенте безличность — жанровая норма, а не слоп. Флаг ставится только
# при высокой плотности, решает всё равно человек.
PASSIVE_RE = re.compile(
    r"(?<!\w)(?:был|была|было|были|будет|будут)\s+"
    r"[а-яё]{3,}(?:ан|ян|ен|ен|т)(?:о|а|ы|ые|ым|ых)?(?!\w)"
    r"|(?<!\w)(?:отмеча|планиру|рекоменду|предполага|осуществля|фиксиру"
    r"|наблюда|ожида|предусматрива|реализу|требу|прогнозиру|подчеркива"
    r"|указыва|разрабатыва|рассматрива)(?:ется|ются)(?!\w)"
    r"|(?<!\w)(?:провод|вид|нахо)(?:ится|ятся)(?!\w)"
    r"|(?<!\w)(?:принято решение|признано целесообразным|проведена работа"
    r"|достигнута договоренность|запланировано|утверждено|обеспечено)(?!\w)"
)

# Притяжательные местоимения: калька с английского (markers-ru.md §11.1).
# Счётчик справочный — судить о лишнем «своём» может только человек.
POSSESSIVE_RE = re.compile(
    r"(?<!\w)(?:"
    r"сво(?:й|я|е|и|ю|его|ей|ему|им|их|ими|ем)"
    r"|наш(?:|а|е|и|у|ю|его|ей|ему|им|их|ими|ем)"
    r"|ваш(?:|а|е|и|у|ю|его|ей|ему|им|их|ими|ем)"
    r"|мо(?:й|я|е|и|ю|его|ей|ему|им|их|ими|ем)"
    r"|тво(?:й|я|е|и|ю|его|ей|ему|им|их|ими|ем)"
    r")(?!\w)"
)


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


def find_fragment_headers(raw: str):
    """Заголовки с подводкой (markers-ru.md §9.6).

    Ищем связку «заголовок → короткая строка, пересказывающая заголовок →
    настоящее содержание». Совпадение по корням (первые пять букв слов
    длиннее четырёх) — грубая, но достаточная замена лемматизации: без неё
    под шаблон попадал бы любой короткий первый абзац.
    """
    heading = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")
    skip = re.compile(r"^\s{0,3}(?:#{1,6}\s|>|[-*+•]\s|\d+[.)]\s|\||```)")
    lines = raw.splitlines()

    def stems(s):
        return {w[:5].lower() for w in WORD_RE.findall(s) if len(w) > 4}

    out = []
    for i, line in enumerate(lines):
        m = heading.match(line)
        if not m:
            continue
        rest = [(j, lines[j]) for j in range(i + 1, len(lines)) if lines[j].strip()]
        if len(rest) < 2:
            continue
        (j, first), (_, second) = rest[0], rest[1]
        if skip.match(first) or skip.match(second):
            continue
        if j + 1 < len(lines) and lines[j + 1].strip():
            continue  # подводка — отдельный абзац, а не первая строка текста
        words = WORD_RE.findall(first)
        if not 1 <= len(words) <= 8:
            continue
        if not stems(m.group(1)) & stems(first):
            continue
        out.append((m.group(1), first.strip()))
    return out


def prose(text: str) -> str:
    """Лёгкая чистка markdown плюс склейка жёстких переносов.

    Абзац, разбитый на строки по 72 символа, иначе считался бы набором
    обрывков: метрики ритма и доля рубленых фраз ломались бы на любом
    тексте из редактора с переносами. Заголовки и буллеты остаются
    отдельными строками, склеиваются только продолжения предложений.
    """
    marker = re.compile(r"^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+•]\s+|\d+[.)]\s+)")
    out = []
    for raw_line in text.splitlines():
        is_marked = bool(marker.match(raw_line))
        line = marker.sub("", raw_line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue
        joinable = (
            out
            and out[-1].strip()
            and not is_marked
            and not re.search(r"[.!?…:;]\s*$", out[-1])
        )
        if joinable:
            out[-1] = out[-1].rstrip() + " " + stripped
        else:
            out.append(stripped)
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
    # Рубленые фразы считаем только по завершённым предложениям: заголовки,
    # пункты списков и подписи к схемам коротки сами по себе и к ритму
    # прозы отношения не имеют.
    ENDS_SENT = re.compile(r"[.!?…][\"'»)\]]*$")
    full = [(s, ln) for s, ln in zip(sentences, lengths) if ENDS_SENT.search(s)]
    n_full = len(full)
    staccato = sum(1 for _, ln in full if ln <= 3)
    staccato_share = staccato / n_full if n_full else 0.0

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
    ellipses = len(ELLIPSIS_RE.findall(text))
    ellipsis_per_1000 = ellipses / n_words * 1000
    absolutes = ABSOLUTE_RE.findall(norm)
    abs_per_1000 = len(absolutes) / n_words * 1000
    possessives = POSSESSIVE_RE.findall(norm)
    poss_per_1000 = len(possessives) / n_words * 1000
    passives = list(PASSIVE_RE.finditer(norm))
    passive_per_1000 = len(passives) / n_words * 1000
    speculations = list(SPECULATION_RE.finditer(norm))
    aphorisms = list(APHORISM_RE.finditer(norm))
    frag_headers = find_fragment_headers(raw)

    # --- индекс ---
    rhythm_low = n_sent >= 8 and cv < 0.35
    golden_high = n_sent >= 8 and golden_share > 0.60
    dash_high = dashes_em >= 4 and dash_per_1000 > 10
    openers_bad = bool(bad_openers)
    bullets_high = bullets >= 8 and bullet_share >= 0.40
    staccato_high = n_full >= 8 and staccato_share >= 0.15
    absolutes_high = len(absolutes) >= 4 and abs_per_1000 > 8
    passive_high = len(passives) >= 6 and passive_per_1000 > 12
    neg_n = len(neg_ru) + len(neg_en)

    score = density + 0.5 * min(neg_n, 4)
    flags = []
    for name, on in [
        ("ровный ритм (CV<0.35)", rhythm_low),
        (">60% предложений в зоне 12–20 слов", golden_high),
        ("серии рубленых фраз (≤3 слов ≥15%)", staccato_high),
        ("длинные тире >10 на 1000 слов", dash_high),
        ("абсолюты >8 на 1000 слов", absolutes_high),
        ("пассив без субъекта >12 на 1000 слов", passive_high),
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
    print(f"  рубленые фразы (≤3 слов): {staccato_share * 100:.0f}% "
          f"({staccato}/{n_full} завершённых предложений); тревога с 15%")
    if bad_openers:
        lst = ", ".join(f"«{w}» ×{c}" for w, c in bad_openers[:5])
        print(f"  повторяющиеся начала: {lst}")
    else:
        print("  повторяющихся начал (3+) нет")
    print()

    print("СЧЁТЧИКИ")
    print(f"  тире: длинных (—) {dashes_em} шт., {dash_per_1000:.1f} на 1000 слов; "
          f"средних (–) {dashes_en} шт.")
    print(f"  многоточия: {ellipses} шт., {ellipsis_per_1000:.1f} на 1000 слов")
    print(f"  буллет-строки: {bullets} ({bullet_share * 100:.0f}% непустых строк)")
    print(f"  абсолюты (всегда/никогда/каждый/ни один): {len(absolutes)} шт., "
          f"{abs_per_1000:.1f} на 1000 слов")
    print(f"  притяжательные (свой/наш/ваш/мой): {len(possessives)} шт., "
          f"{poss_per_1000:.1f} на 1000 слов — справочно, лишние ищите глазами")
    print(f"  пассив без субъекта («было принято», «отмечается»): "
          f"{len(passives)} шт., {passive_per_1000:.1f} на 1000 слов; "
          f"тревога с 12 — но в приказе и протоколе это норма жанра")
    for m in passives[:3]:
        print(f"      {context(text, m.start(), m.end())}")
    print(f"  «не X, а Y»-паттерны: RU {len(neg_ru)}, EN {len(neg_en)}")
    for m in neg_ru[:3] + neg_en[:3]:
        print(f"      {context(text, m.start(), m.end())}")
    print(f"  догадки и черновиковые обороты («казалось бы», «судя по всему»): "
          f"{len(speculations)} шт. — справочно, маркер только в связке "
          f"с пробелом в данных или отвергнутым вариантом")
    for m in speculations[:3]:
        print(f"      {context(text, m.start(), m.end())}")
    print(f"  афоризм-формулы («X — язык Y», «становится ловушкой»): "
          f"{len(aphorisms)} шт. — справочно, судить по контексту")
    for m in aphorisms[:3]:
        print(f"      {context(text, m.start(), m.end())}")
    print(f"  заголовки с подводкой: {len(frag_headers)} шт.")
    for head, lead in frag_headers[:3]:
        print(f"      «{head}» → «{lead}»")
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
