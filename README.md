# База данных биоактивности из PDF

Воспроизводимый пайплайн для извлечения, очистки и стандартизации данных о биоактивности соединений из научных статей в формате PDF. Методология соответствует принципам лекции «Анализ, очистка и стандартизация химических данных» (файл `Анализ, очистка и стандартизация химических данных.pptx`).

## Результат

| Артефакт | Описание |
|----------|----------|
| [`build_database.py`](build_database.py) | Точка входа пайплайна |
| [`data/chemical_database.csv`](data/chemical_database.csv) | Итоговая БД (~220 записей) |
| [`data/qc_report.csv`](data/qc_report.csv) | Отчёт контроля качества |
| [`data/pubchem_cache.json`](data/pubchem_cache.json) | Кэш ответов PubChem |

## Источники данных

В проекте **8 PDF-статей** по медицинской химии (опиоидные рецепторы, NPSR, CB1):

| PDF | Содержание | Метод извлечения |
|-----|------------|------------------|
| `1-s2.0-S0960894X08008214-main.pdf` | Ki опиоидных лигандов (µ, δ, κ) | pdfplumber, таблица |
| `1-s2.0-S0960894X09003679-main.pdf` | NOP/MOP Ki, EC50 (GTPγS) | pdfplumber, таблицы |
| `1-s2.0-S0960894X09006222-main.pdf` | Ki/IC50 пептидов κ/µ/δ | pdfplumber, таблица |
| `1-s2.0-S0960894X09006258-main.pdf` | ORL1/hERG IC50 | pdfplumber, таблицы |
| `1-s2.0-S0223523412000402-main.pdf` | Ki в тексте статьи | regex по прозе |
| `design-synthesis-...-naltrexamine-...pdf` | Ki MOR/DOR/KOR, Table 2 | pymupdf, построчный парсер |
| `further-studies-at-neuropeptide-s-...pdf` | pEC50/pKB NPS аналогов | координаты слов + проза |
| `synthesis-and-evaluation-of-dibenzothiazepines-...pdf` | pKi/pIC50 CB1 | проза (таблицы — изображения) |

## Пайплайн обработки

Соответствие этапов слайдам лекции:

```
PDF → Извлечение → Стандартизация → PubChem → QC → CSV
       (слайд 3)    (слайды 6–8)     (слайд 15)  (слайд 24)
```

1. **Извлечение** (`src/extract/`) — создаёт сырые записи из таблиц (pdfplumber), текста (pymupdf) и прозы (regex). Сохраняются фрагменты с привязкой к источнику: PDF, страница, таблица.

2. **Стандартизация** (`src/standardize/`) — по слайду 7:
   - каноническая единица концентрации: **nM**;
   - исходные `value_raw` / `unit_raw` не перезаписываются;
   - pKi/pIC50/pEC50 остаются в log-шкале (`unit_std = pX`).

3. **Стандартизация мишеней** (`config/target_mapping.json`) — по слайдам 8, 14: MOR→OPRM1, NOP→OPRL1, CB1→CNR1 и т.д.

4. **Разрешение структур** (`src/resolve/pubchem.py`) — по слайду 15: для известных имён (naltrexone, rimonabant, CTAP…) запрос к PubChem REST API с локальным кэшем.

5. **Контроль качества** (`src/validate/qc.py`) — по слайдам 17, 21–24:
   - дедупликация уровня 1 (точные дубликаты);
   - группы конфликтов (`conflict_group_id`) без усреднения значений;
   - флаги `valid` / `suspicious` / `manual_review`.

## Схема CSV

Одна строка = одно измерение (соединение × мишень × endpoint × контекст).

| Группа | Столбцы |
|--------|---------|
| Источник | `record_id`, `source_pdf`, `source_doi`, `source_page`, `source_table`, `extraction_method` |
| Соединение | `compound_id`, `compound_name`, `smiles_raw`, `inchikey`, `pubchem_cid`, `structure_resolution` |
| Активность (raw) | `endpoint_raw`, `value_raw`, `unit_raw`, `sem_raw`, `qualifier` |
| Активность (std) | `endpoint_std`, `value_std`, `unit_std`, `conversion_note` |
| Контекст | `target_raw`, `target_std`, `assay_type_raw`, `assay_type_std`, `organism`, `cell_line`, `conditions` |
| QC | `validation_status`, `duplicate_level`, `conflict_group_id`, `notes` |

### Правила стандартизации единиц

| Исходная единица | Каноническая | Пример |
|------------------|--------------|--------|
| nM | nM | 12 nM → 12 nM |
| µM | nM | 0.012 µM → 12 nM |
| pM | nM | 48 pM → 0.048 nM |
| pKi, pIC50 | pX | без пересчёта |

### Пропущенные и особые значения

| Маркер | Значение |
|--------|----------|
| `nd` | не определено |
| `>` / `<` | предел детекции, сохраняется в `qualifier` |
| `c` | Ki > 1000 nM (из оригинальной таблицы) |

## Запуск

```bash
pip install -r requirements.txt
python build_database.py
```

Опции:

```bash
python build_database.py --no-pubchem          # только кэш PubChem, без сети
python build_database.py --output data/my.csv  # другой путь вывода
```

## Ограничения

По слайду 16 лекции — не всё поддаётся автоматизации:

- **Таблицы-изображения** в ACS-статьях (neuropeptide Table 1, dibenzothiazepines Table 1–3): извлечены только значения из текста статьи, записи помечены `manual_review`.
- **Числовые ID соединений** (`4b`, `12e`) без химического имени: `structure_resolution = unresolved`.
- **Пептиды** (`[tBu-D-Gly5]NPS`): `structure_resolution = peptide_sequence_only`.
- **Конфликты** между Ki и IC50 для одного соединения не объединяются — разные `endpoint_std` (слайд 31).

## QC-отчёт

Файл `data/qc_report.csv` содержит:

- `raw_records` / `final_records` — до и после дедупликации;
- `duplicates_merged` — точные дубликаты (уровень 1);
- `conflict_groups` — группы с расхождением >2× при одинаковом контексте;
- `manual_review` — записи из прозы или image-only таблиц;
- `suspicious` — отсутствие значения, ошибка конверсии единиц.

## Структура кода

```
├── build_database.py
├── config/target_mapping.json
├── requirements.txt
├── src/
│   ├── extract/          # парсеры PDF
│   ├── standardize/      # единицы, мишени, типы анализа
│   ├── resolve/          # PubChem
│   ├── validate/         # QC
│   └── export.py
└── data/
    ├── chemical_database.csv
    ├── qc_report.csv
    └── pubchem_cache.json
```

## Лицензия данных

Исходные статьи защищены авторским правом издателей. Производная база данных предназначена для учебных целей; при повторном использовании необходимо указывать первичные источники (`source_pdf`, `source_doi`).
