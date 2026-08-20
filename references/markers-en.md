# Маркеры английского нейрослопа: словарь

Дополнение к markers-ru.md для англоязычных текстов и для распознавания
калек в русском. Те же три правила: маркер — вероятность, а не приговор;
запрет только в связке с заменой; словарь пересматривать каждые несколько
месяцев — модели учатся обходить известные слова.

## 1. Слова-сигнатуры (с корпусной статистикой)

| Маркер | Что известно | Русский эквивалент/аналог |
|---|---|---|
| delve (into) | Маркер №1. Shapira (168 млн записей OpenAlex): 0,056% рефератов (2022) → 0,278% (2023) → 0,793% (Q1 2024), рост ×14; всплеск в PubMed после ChatGPT (Matsui 2024); «excess word» у Kobak et al. | «углубляться», «погружаться», «глубокое погружение» |
| crucial | Один из сильнейших excess words; у Мельничук ×36 у ИИ против 0 у журналистов | «ключевой», «критически важный» |
| pivotal | Excess word (Kobak) | «переломный», «ключевой» |
| intricate(ly) | Excess word (Kobak) | «замысловатый», «многогранный» |
| meticulously | Excess word (Kobak) | «скрупулёзно», «тщательно» |
| commendable, noteworthy | Excess words (Kobak) | «достойный внимания/похвалы» |
| tapestry («rich tapestry of…») | Мем-маркер декоративной метафоры | «богатая палитра/мозаика» |
| testament («a testament to…») | Псевдоторжественность | «служит свидетельством» |
| landscape («in the ever-evolving landscape of…») | Шаблонное вступление | «в ландшафте», «в условиях современного…» |
| realm («in the realm of…») | Декоративная абстракция | «в сфере», «в мире…» |
| furthermore, moreover, additionally | Избыток коннекторов; в прессе почти отсутствуют, у ИИ перепредставлены (Мельничук) | «более того», «кроме того» |
| notably, importantly, significantly | Оценочные наречия-усилители | «важно отметить», «примечательно» |
| underscore, highlight, emphasize («this underscores the importance of…») | Дежурные глаголы «значимости» | «подчёркивает важность» |
| navigate («navigate the complexities of…») | Дежурная метафора | «разобраться в тонкостях» |
| embark (on a journey), journey, unleash, unlock, elevate, harness, foster, garner, boast | Промо-лексика «восторга» (wiki-гайд) | «отправиться в путешествие», «раскрыть потенциал», «вывести на новый уровень» |
| vibrant, rich, diverse («vibrant community», «rich cultural heritage») | Дежурные эпитеты без конкретики | «богатое наследие», «неповторимая атмосфера» |
| seamless, holistic, nuanced, multifaceted, comprehensive, robust | Корпоративно-энциклопедические эпитеты | «бесшовный», «комплексный», «многогранный» |
| ever-evolving, fast-paced, dynamic («in today's fast-paced world») | Штамп «стремительности» | «в стремительно меняющемся мире» |
| game-changer, groundbreaking, revolutionary, cutting-edge, state-of-the-art | Промо-гиперболы | «прорывной», «революционный» |
| beacon («stands as a beacon of…») | Декоративная метафора значимости | «сияющий пример», «маяк» |
| imagine, picture this («Imagine a world where…») | Дежурный хук вовлечения | «представьте себе» |
| utilize, leverage, facilitate, in order to, due to the fact that | Псевдоформальные заменители use/help/to/because | канцелярит вместо простых слов |
| curate, showcase | Промо-глагольный фонд | «тщательно отобранный», «продемонстрировать» |

Перечастотные фразы по данным GPTZero (Forbes ведёт обновляемый список):
«provide a valuable insight» — в 468 раз чаще в AI-текстах, «left an
indelible mark» — ×317, «play a significant role in shaping» — ×207,
«an unwavering commitment» — ×202.

## 2. Фразы-клише (sentence-level)

- «In today's world / In the digital age / In today's fast-paced world» → «в современном мире», «в эпоху цифровизации».
- «It's important to note that… / It's worth noting that…» → «важно отметить», «стоит отметить».
- «In conclusion / In summary / Overall / Ultimately / At its core» → «в заключение», «подводя итог», «по сути».
- «serves as a testament to / stands as a symbol of / is a shining example of» → «служит свидетельством», «яркий пример».
- «plays a (vital/crucial/key) role in…» → «играет ключевую роль».
- «has a profound/significant impact on…» → «оказывает значительное влияние».
- «from X to Y»: «from beginners to experts» → «от новичков до профессионалов».
- «whether you're a X or a Y…» → «будь то X или Y».
- «It's not just X, it's Y / It's not about X, it's about Y» (negative parallelism) → ЖЁСТКИЙ БАН, как и русская версия.
- «not only… but also…» — в норме, но гиперчастотно в GPT-текстах.
- «Let's dive in / Let's explore / Let's break it down» → «давайте разберёмся».
- Пустые финалы: «The future looks bright / Only time will tell / Exciting times ahead» → «время покажет».
- Диалоговые восторги: «Certainly! / Absolutely! / Great question!» → «Отличный вопрос!».
- Назидание: «Remember, …» / «Keep in mind that…» → «помните, что…».
- Расплывчатая атрибуция: «experts say / studies show / critics argue / many believe» → «эксперты считают», «исследования показывают».
- «As an AI language model…» — устаревший, но встречающийся самослив.
- Чат-артефакты: «I hope this helps!», «Here's a draft…», «Would you like me to…».
- Дежурный финал-раздел: «Despite these challenges…», «Challenges and Legacy», «Future Outlook», «continues to thrive» → §9.8 markers-ru.md.
- Значимость через витрины: «has been cited in major outlets», «maintains an active social media presence», «written by a leading expert» → §3.1.
- Догадка вместо пробела: «While specific details are limited…», «it is believed that», «likely grew up/studied», «maintains a low profile», «prefers to stay out of the spotlight» → §7.1.
- Оборона от невысказанного: «I'm not saying that…», «Don't get me wrong», «To be clear», «This isn't really about…», «Some might say… but» → §9.9.
- Фальшивая альтернатива: «A tempting approach would be…», «One might be tempted to…», «An obvious approach would be…, but», «It would be easy to just…» → §9.10.

## 3. Структурные паттерны

- **Negative parallelism** («It's not X, it's Y», «No X. No Y. Just Z.») — один из самых цитируемых синтаксических маркеров. Жёсткий бан.
- **Rule of three**: «innovation, inspiration, and insights» — тройки в каждом абзаце.
- **Copula avoidance**: «serves as / functions as / stands as / represents» вместо повторного «is».
- **Synonym cycling**: «the city — this vibrant metropolis — the urban area» — механическая ротация синонимов (побочка repetition penalty).
- **Хвостовые -ing-придатки**: «…, highlighting the importance of…», «…, underscoring the significance of…», «…, reflecting the growing trend».
- **Пустые подлежащие**: «It is worth noting that…», «There is no doubt that…».
- **Ложные диапазоны**: «from the Big Bang to dark matter» — несоизмеримые концы.
- **Эм-тире** для драматических вставок — самый мемный типографский маркер; частота у ИИ в 3–5 раз выше человеческой нормы. Дозировать, не вычищать под ноль.
- **Passive with missing subject**: «No configuration file needed», «The results are preserved automatically» — действие есть, действующего нет. Русский эквивалент — §8.12 markers-ru.md.
- **Repeated sentence openings**: «She noted the door. She noted the lock. She filed both away.» Зеркало synonym cycling: там ротация, здесь долбёж. Русский эквивалент — §8.11.
- **Hyphenated pairs**: «cross-functional, data-driven, client-facing» гроздьями; дефис нужен перед существительным («a high-quality report») и не нужен после него («the report is high quality»). Английская болезнь, на русский не переносится.
- **Разметка**: Title Case в заголовках, болд почти в каждом абзаце, inline-header списки («**Term:** description»), эмодзи, curly quotes.

## 4. Примеры «до → после» (EN)

> До: «In today's fast-paced world, effective communication plays a crucial
> role in professional success. Furthermore, it serves as a testament to
> one's dedication».
> После: «My talk bombed at the 2023 offsite — 12 slides, zero questions.
> This year I brought one chart and a story; people argued for an hour».

> До: «This innovative solution not only streamlines workflows but also
> fosters collaboration, highlighting the importance of synergy».
> После: «The tool cut our review cycle from 5 days to 2. Whether it helps
> "synergy" — ask the three teams still refusing to use it».

## 5. Ориентиры по статистике (для понимания масштаба)

- Perplexity: человек ~105–165 против ИИ ~47–60 на рефератах; у GPT-4 ~20–30.
- Burstiness (дисперсия длины предложений): человек 0,6–1,2 против 0,2–0,4 у GPT.
- Длина предложений: у человека 3–40+ слов с хаотичной амплитудой, у ИИ ровно 12–20 (Грамота.ру).
- Порог-ориентир самого GPTZero: perplexity выше ~85 — скорее человек.

Цифры — ориентиры из детекционной литературы, а не цели для подгонки.
Текст, подогнанный под метрики без живого содержания, остаётся слопом.

## 6. Чего не переносить на русский

Англоязычные анти-слоп руководства (в том числе Wikipedia «Signs of AI
writing» и построенные на ней навыки) содержат типографские правила, которые
на русском тексте вредят. Проверяйте язык, прежде чем применять:

- **Запрет на тире.** В английском em dash — необязательный знак, и его
  избыток действительно маркер. В русском тире обязательно в неполном
  предложении и при пропуске связки («Москва — столица»), это норма, а
  не след машины. Правило одно: дозировать (§8.7 markers-ru.md), а не
  вычищать.
- **Прямые кавычки вместо «ёлочек».** Совет из английских гайдов; в русской
  типографике кавычки-ёлочки — стандарт, а „лапки" — вложенный уровень.
  Curly quotes маркером считаются только в английском тексте.
- **Title Case.** Русские заголовки и так пишутся с одной прописной, ловить
  нечего. Флаг работает только на английском.
- **Дефисные пары.** Правило про «high-quality report» / «report is high
  quality» относится к английской орфографии и в русском смысла не имеет.

Обратное тоже верно: раздел §11 markers-ru.md (кальки, лишние
притяжательные, корпоративный жаргон) на английском тексте бессмысленен.

---

## Источники

1. Wikipedia (EN): «Signs of AI writing» — https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
2. Shapira P. «Delving into “delve”» (анализ OpenAlex) — https://pshapira.net/2024/03/31/delving-into-delve/
3. Kobak D. et al. «Delving into ChatGPT usage in academic writing through excess vocabulary» — https://arxiv.org/abs/2406.07016
4. Matsui A. «Delve: a single word can detect AI-generated text?» — https://arxiv.org/abs/2407.08935
5. GPTZero: «How To Avoid AI Detection As A Student» (список перечастотных фраз, порог perplexity) — https://gptzero.me/news/how-to-avoid-ai-detection-as-a-student/
6. Мельничук А. О. (2024), частотная таблица слов — http://e-lib.bsufl.by/bitstream/edoc/16637/1/191-195.pdf
7. Juzek T., Ward Z. «Why does ChatGPT use “Delve” so much?» — https://arxiv.org/abs/2505.01050
8. Грамота.ру: «Как распознать ИИ-текст» — https://gramota.ru/journal/stati/tekhnologii/chem-sgenerirovannye-teksty-vydayut-sebya
