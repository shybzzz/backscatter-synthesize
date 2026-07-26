---
name: readme
description: Generate or update README.md for this project. Use whenever README.md is created, extended with a new model stage, or edited — it defines the required language (Ukrainian), academic-engineering style, enumeration rules for formulas/figures/tables, and NDT terminology.
---

# README generation for backscatter-synthesize

The README documents the signal-synthesis model for the project owner's postgraduate student. It must read like a concise engineering text with a slightly academic tone.

**Audience filter**: not everything the owner says belongs in the README. Hypotheticals, sanity checks, and examples the owner addresses to the assistant («evaluate this X of mine», «what if ...») are conversation material — answer them in chat and do NOT write them into the document unless the owner asks. When unsure whether a discussion is for the student document or for the conversation, ASK before adding it.

## Language and style

- Write in **Ukrainian**. Code identifiers, commands, and file names stay in English.
- Engineering style, slightly academic: precise terminology, short justifications for modelling choices (why a parameter value was chosen, what physical effect it reproduces), no marketing language.
- Use Ukrainian typographic conventions: decimal comma in prose and math ($1{,}1\%$, $6{,}8$), apostrophe in words like «п'єзоелектричний», quotation marks «...».
- Abbreviations MUST be expanded at first use — «повна назва (АБРЕВІАТУРА)» — and may be used alone afterwards. Applies to Ukrainian and Latin abbreviations alike (СКЗ, АЦП, ПММА, ШІ, SJR). Exempt: SI units (дБ, МГц, мкс) and standard bibliographic marks (DOI). Specialist terms that read like codes (А-скан) get a short parenthetical gloss at first use.

## Terminology (use exactly these terms)

| English | Ukrainian |
|---|---|
| dual-element (pitch-catch) probe | роздільно-суміщений перетворювач |
| excitation pulse / tone burst | зондувальний імпульс / радіоімпульс |
| carrier frequency | частота заповнення |
| envelope | обвідна |
| sample rate | частота дискретизації |
| sample (index) | відлік (номер відліку) |
| backwall echo | донний сигнал |
| flaw | дефект |
| grain noise | структурний шум |
| attenuation | загасання |
| impulse response | імпульсна характеристика |
| NDT | неруйнівний контроль |

## Referencing claims

Every modelling assumption or conclusion stated in the README must be backed by a citation «[n]» to the «Джерела» list — e.g. a claim that a model is standard practice, a chosen parameter value, a physical simplification, or an accepted convention (like the $-6$ дБ bandwidth reference level). If no trustworthy source can be found, do not present the statement as established fact: either mark it explicitly as a working assumption of this project or ask the owner.

ALWAYS cite any physical law, named relation, or formula imported from outside the document at the exact place it is first stated — including inside explanatory or "intuitive" passages (e.g. $T = 4Z_1Z_2/(Z_1+Z_2)^2$, Stokes relations, $I \propto p^2/Z$). The no-citation exemption covers ONLY algebraic steps that transform formulas already numbered and cited in this README; any new physical input entering a derivation needs its own citation. Verify every cited URL by fetching it (or its DOI metadata) before adding; prefer sources whose exact statement of the formula was actually seen, and cite the page/section when the source is long.

## Formulas

- LaTeX in `$$...$$` blocks; inline math in `$...$`.
- Numbering: TEMPORARILY (GitHub-compatibility fix of 2026-07-26, see CLAUDE.md "Known issues") formulas are numbered with a literal `\qquad (n)` as the last line inside the `$$` block, NOT with `\tag{n}`. Avoid `\!`. Use this same form for new formulas until the owner decides to revert to `\tag{n}`.
- Every symbol used in a formula or in prose must be defined at first use (e.g. «де $k = 0, 1, 2, \dots$ — номер відліку»).
- NEVER present a formula bare: every numbered formula must be accompanied by explicit reasoning in prose — either a derivation sketch from already-numbered-and-cited formulas of this document (name them: «за співвідношенням Стокса (6)», «з $R = r^2$ [10]»), or a citation to the external source it is imported from. A formula whose origin the reader cannot reconstruct is a defect; the owner has flagged this twice.
- Reference formulas in text by number: «(1)», «згідно з (2)».
- Nontrivial parameter choices get their own numbered formula plus a one-sentence justification.

## Enumeration of figures and tables

- **Figures**: image, then a bold caption line *below* it: `**Рис. n.** <опис>`. Reference in text as «(рис. n)».
- **Tables**: bold caption line *above* the table: `**Таблиця n.** <опис>`. Reference in text as «таблиці n».
- Numbering of formulas, figures, and tables is continuous through the whole document. When inserting new material in the middle, renumber everything after it, including all in-text references.
- A section must NEVER end with an image, table, formula, or bare caption — always close with at least one sentence of prose (interpretation of the figure, a consequence, or a transition to the next stage). Keep captions to a concise identification of what is shown; put the interpretive discussion (what the reader should see, notable features, practical implications) in body text after the figure.
- **Multi-panel figures**: every panel carries an italic Cyrillic letter (а, б, в, г, д, ...) in its corner — `plot_signals` in `backscatter/visualization.py` adds these automatically. The figure caption MUST decode every letter: `**Рис. n.** <опис>: а — <панель 1>; б — <панель 2>; ...`. Reference an individual panel in text as «(рис. n, а)». Never describe panels positionally («згори», «середня панель») — use the letters.

## Document structure

BEFORE editing README.md, ALWAYS look at the «## Зміст» table of contents first to understand the document structure and find the correct insertion point — do not guess a section's position from nearby text (a new numbered chapter goes after the last numbered chapter and BEFORE the service sections). Update «Зміст» in the same edit whenever a section is added, renamed, or moved.

1. Title `# backscatter-synthesize` and a short purpose paragraph (dual-element transducer, NDT, model built incrementally).
2. `## Зміст` — table of contents: numbered chapters as a numbered list with GitHub anchor links, then one line «Службові розділи: ...» linking the service sections. Anchors: lowercase, spaces → hyphens, punctuation dropped.
3. One numbered section per model stage (`## 1. Зондувальний імпульс`, `## 2. ...`) in signal-chain order: excitation pulse → transducer impulse response → propagation medium → reflectors/scatterers → receive path. Each section: physical description, formula(s), parameter table with defaults, generated figure(s) from `images/`.
4. `## Структура проєкту` — file tree with one-line descriptions.
5. `## Використання` — install/run commands and a minimal Python API example.
6. `## План розвитку` — numbered roadmap; completed stages struck through (`~~...~~`) with «(виконано)».
7. `## Огляд споріднених досліджень` — literature table with DOIs, journal links, citation counts and quartiles, dated.
8. `## Джерела` — numbered reference list. Cite in text as «[n]» (e.g. after the formula or claim the source supports). Only authoritative, verifiable sources with working web links: textbooks/papers with a DOI link, official library documentation (SciPy, MATLAB, k-Wave, Field II). Verify each URL resolves before adding it. Format: Author. *Title.* — edition. — Publisher, year. — DOI/link; for library docs: `function` — one-line description // Documentation name. — link.

## Workflow when a model stage changes

1. Run `python main.py` (with `MPLBACKEND=Agg` when headless) to regenerate figures in `images/` so README embeds match the code.
2. Update the affected section, parameter tables, and default values against the actual code — never document values that differ from the module constants.
3. Update the roadmap checklist.
4. Check enumeration continuity (formulas, figures, tables, and their in-text references).
