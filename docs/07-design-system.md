# 07 — Design System

## 1. Direction

**Warm & editorial.** The site should feel like a well-made independent magazine about animals, not a pet shop and not a SaaS dashboard. Photography leads; typography is confident; whitespace is generous; the interface gets out of the way of the animal.

The reason is commercial as much as aesthetic. Adoption is an emotional decision made under a nagging worry — *am I doing this right?* A calm, considered, editorial surface signals that the organisation on the other end is serious. A bright playful interface undercuts that, and a grey SaaS grid makes living animals look like inventory.

**Principles**

1. **The animal is the interface.** The largest element on any screen showing an animal is that animal's photograph. Chrome shrinks; the photo does not.
2. **Honesty over polish.** An unknown behaviour trait is shown as unknown. A long wait is shown as a long wait. We never round a hard fact into a warm one.
3. **Calm density.** Shelter screens carry real data and must stay legible at 60 rows. Density comes from tightening space, never from shrinking type below 14 px or dropping contrast.
4. **One accent.** A single accent colour carries actions. When everything is emphasised, the "adopt" button stops meaning anything.
5. **Motion is feedback, never decoration.** 120–200 ms, ease-out, and nothing moves that the user did not cause.

The shelter back-office uses the same tokens as the public site but a tighter spacing scale and more neutral surfaces. It should feel like the same product with its sleeves rolled up — not a second application.

## 2. Colour

Semantic tokens only. No component ever names a raw colour.

### Light (default)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#FBF8F3` | Page background — warm cream, not white |
| `--surface` | `#FFFFFF` | Cards, panels |
| `--surface-sunken` | `#F3EEE6` | Wells, table stripes, empty states |
| `--border` | `#E4DCD0` | Hairlines |
| `--border-strong` | `#CBBFAE` | Input borders, dividers that must read |
| `--text` | `#1F1B16` | Primary text |
| `--text-muted` | `#6B6157` | Secondary text, captions |
| `--text-subtle` | `#8F857A` | Metadata, placeholders |
| `--accent` | `#B4531F` | Terracotta — primary actions, links |
| `--accent-hover` | `#96421A` | |
| `--accent-soft` | `#F7E9DF` | Accent-tinted backgrounds |
| `--accent-text` | `#8A3D16` | Accent text on light backgrounds (AA on `--bg`) |
| `--forest` | `#2F5D4A` | Secondary — success, "available", shelter chrome |
| `--forest-soft` | `#E4EFE9` | |
| `--success` | `#2F6B45` | Confirmations |
| `--warning` | `#9A6B12` | Attention, stale data, expiring |
| `--danger` | `#A3301F` | Destructive, rejection |
| `--info` | `#2B5A80` | Neutral information, AI-generated labels |
| `--focus` | `#1F6FEB` | Focus ring — deliberately distinct from the accent |

### Dark

| Token | Value |
|---|---|
| `--bg` | `#16130F` |
| `--surface` | `#221D18` |
| `--surface-sunken` | `#1B1713` |
| `--border` | `#332C24` |
| `--border-strong` | `#4A4036` |
| `--text` | `#F2EDE6` |
| `--text-muted` | `#B5A99B` |
| `--text-subtle` | `#8B7F72` |
| `--accent` | `#E0813F` |
| `--accent-hover` | `#EE9755` |
| `--accent-soft` | `#3A2517` |
| `--forest` | `#5FA07C` |
| `--success` | `#5FA07C` · `--warning` `#D4A24C` · `--danger` `#E07A66` · `--info` `#7FB0D6` |
| `--focus` | `#5A9BFF` |

Dark mode follows the system preference with a manual override. Every pairing in use must clear WCAG AA — 4.5:1 for body text, 3:1 for large text and UI boundaries — verified in CI by a contrast test over the token pairs the components actually use, not by eye.

### Status colours

Animal status is never conveyed by colour alone: every chip carries a label and, where space allows, an icon.

| Status | Treatment |
|---|---|
| `available` | Forest chip, "Disponibile" |
| `reserved` | Warning chip, "Prenotato" |
| `adopted` | Muted chip with a small home icon, "Adottato" |
| `unavailable` | Subtle outline chip with the reason |
| `draft` | Dashed outline chip, shelter-only |

## 3. Typography

| Role | Family | Notes |
|---|---|---|
| Display / headings | **Fraunces** (variable serif) | Optical size and slight softness; carries the editorial tone |
| Body / UI | **Inter** (variable) | Excellent at small sizes, full Italian diacritics |
| Numeric / data | Inter with `font-variant-numeric: tabular-nums` | Dashboard figures must align |

Both self-hosted, subset to Latin + Latin Extended-A, `font-display: swap`, variable axes to avoid multiple files. No external font CDN — it is a third-party request on every page for no benefit and a GDPR question we do not need.

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `display-xl` | 56/60 (mobile 40/44) | 600 Fraunces | Home hero |
| `display-l` | 40/46 (mobile 32/38) | 600 Fraunces | Page titles |
| `heading-l` | 28/34 | 600 Fraunces | Section titles |
| `heading-m` | 22/28 | 600 Inter | Card titles, animal names |
| `heading-s` | 18/24 | 600 Inter | Subsections |
| `body-l` | 17/28 | 400 Inter | Long-form: stories, guides |
| `body` | 15/24 | 400 Inter | Default UI |
| `body-s` | 13/20 | 400 Inter | Metadata, captions |
| `label` | 13/16 | 500 Inter, `0.02em` | Form labels, chips |
| `mono` | 13/20 | JetBrains Mono | References, microchip numbers |

Measure caps at 68 characters for long-form. Headings use `text-wrap: balance`.

## 4. Space, radius, elevation

4 px base scale: `0.5 1 1.5 2 3 4 6 8 12 16 24` → `2 4 6 8 12 16 24 32 48 64 96` px.

Public pages use the generous end (section padding 64–96 px desktop, 32–48 mobile). Shelter screens use the tight end (section padding 24–32, table rows 44 px).

Radii: `sm 6` (chips, inputs) · `md 10` (buttons, small cards) · `lg 16` (cards, dialogs) · `xl 24` (hero media, feature panels) · `full` (avatars, pills).

Elevation is restrained — three levels, warm-tinted rather than neutral grey, because a grey shadow on a cream surface reads as dirt:

```
--shadow-sm: 0 1px 2px rgba(31,27,22,.06), 0 1px 1px rgba(31,27,22,.04);
--shadow-md: 0 4px 12px rgba(31,27,22,.08), 0 1px 3px rgba(31,27,22,.05);
--shadow-lg: 0 12px 32px rgba(31,27,22,.12), 0 2px 8px rgba(31,27,22,.06);
```

In dark mode elevation is expressed by surface lightness, not shadow.

## 5. Components

Built on shadcn/ui (Radix primitives copied into the repo and restyled). We inherit the accessibility work — focus management, ARIA, keyboard handling — and replace the visual layer entirely with our tokens.

### Restyled primitives
Button, Input, Textarea, Select, Combobox, Checkbox, Radio, Switch, Slider, Dialog, Sheet, Popover, Tooltip, Tabs, Accordion, Toast, Badge, Avatar, Skeleton, Progress, Calendar, Table, Pagination, Dropdown menu, Command palette.

### Product components

| Component | Notes |
|---|---|
| `AnimalCard` | Photo 4:3 with blur placeholder, name, age·size·sex line, status chip, distance, optional match badge, favourite toggle. The whole card is one link; the favourite button is a nested button with its own label. |
| `AnimalCardCompact` | Horizontal, for lists, digests, and the assistant's inline results. |
| `MatchScoreBadge` | Score, band colour, tooltip listing the top contributing dimensions. |
| `MatchBreakdown` | Eight horizontal bars, one per dimension, with weight and contribution — the visual form of the table in [06](./06-matching-algorithm.md). |
| `BehaviorGrid` | Behaviour fields as icon + statement pairs. `unknown` renders in `--text-subtle` with a dashed border and the word "Non testato" — visually distinct from both yes and no. |
| `MediaGallery` | Keyboard-navigable, arrow keys and swipe, video with poster and no autoplay-with-sound, full-screen view with escape. |
| `FilterBar` | Collapsible on mobile into a sheet; active filters render as removable chips; URL-synced. |
| `MapView` | Leaflet, clustered markers, animal preview on marker click, "search this area" control; lazy-loaded. |
| `QuizStep` | One question, large touch targets, progress bar, back always available, "non lo so" always present. |
| `KPITile` | Label, big tabular figure, delta versus previous period with direction, sparkline, links to the filtered list behind it. |
| `AtRiskRow` | Photo, name, days waited, probability, expected band, top factors as chips, suggested actions as dismissible buttons. |
| `PredictionCard` | Probability, expected band, factors, model version and date, and a permanent caveat line. Never rendered on a public page. |
| `StatusTimeline` | Application progress; completed steps solid, current step accented, future steps outlined; each entry dated. |
| `ApplicationCard` | Queue row with applicant summary, animal thumbnail, status, age of the application (highlighted past the shelter's target response time). |
| `SlotPicker` | Week grid, remaining capacity per slot, unavailable slots visibly disabled with a reason. |
| `MedicalTimeline` | Reverse-chronological entries by type with icons, weight chart, upcoming due badges. |
| `ChatWidget` | Floating launcher, expandable panel, streaming text, inline animal cards, citation links, and a persistent "assistente AI" label. |
| `AIDisclosure` | Small `--info` chip reading "Testo generato con AI" / "Stima del modello", attached to every generated or predicted value. Never optional. |
| `EmptyState` | Illustration, one clear sentence, one action. Never a bare "Nessun risultato". |
| `ConsentBanner` | Cookie categories with genuinely equal accept/reject prominence. |

## 6. Key screens

### Home

```
┌──────────────────────────────────────────────────────────────┐
│ PetMatch AI    Animali  Strutture  Guide      IT/EN  Accedi  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────────────┐   Ogni animale ha già             │
│   │                      │   una famiglia.                   │
│   │   [full-bleed photo] │   Deve solo incontrarla.          │
│   │                      │                                   │
│   │                      │   Rispondi a 14 domande oneste e  │
│   │                      │   ti mostriamo gli animali che    │
│   └──────────────────────┘   davvero si adattano alla tua    │
│                              vita. Spiegando sempre perché.  │
│                                                              │
│                              [ Trova il tuo match → ]        │
│                              [ Sfoglia tutti gli animali ]   │
├──────────────────────────────────────────────────────────────┤
│  1.243 animali in cerca di casa   ·   48 strutture   ·  …    │
├──────────────────────────────────────────────────────────────┤
│  Aspettano da più tempo                        [vedi tutti → ]│
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                 │
│  │ photo  │ │ photo  │ │ photo  │ │ photo  │                 │
│  │ Rocco  │ │ Nina   │ │ Bruno  │ │ Mia    │                 │
│  │ 8 anni │ │ 3 anni │ │ 5 anni │ │ 7 anni │                 │
│  │ 418 gg │ │ 302 gg │ │ 288 gg │ │ 265 gg │                 │
│  └────────┘ └────────┘ └────────┘ └────────┘                 │
├──────────────────────────────────────────────────────────────┤
│  Come funziona                                               │
│   1 Rispondi   →   2 Scopri i match   →   3 Candidati        │
├──────────────────────────────────────────────────────────────┤
│  Sei una struttura?  Gestisci i tuoi animali gratis. [Scopri]│
└──────────────────────────────────────────────────────────────┘
```

Leading with animals who have waited longest, rather than the cutest puppies, is a product decision with a design consequence: the home page's most valuable slot serves the animals the platform exists for.

### Browse

```
┌──────────────────────────────────────────────────────────────┐
│ ┌──────────────┐  1.243 animali        [◫ Griglia] [◉ Mappa] │
│ │ Specie       │  Ordina: [Più vicini ▾]                     │
│ │ ☑ Cane ☐Gatto│  ┌────────┐ ┌────────┐ ┌────────┐          │
│ │              │  │        │ │        │ │        │          │
│ │ Taglia       │  │ photo  │ │ photo  │ │ photo  │          │
│ │ ☑ Piccola    │  │        │ │   ♥    │ │        │          │
│ │ ☑ Media      │  ├────────┤ ├────────┤ ├────────┤          │
│ │ ☐ Grande     │  │ Luna   │ │ Nina   │ │ Kira   │          │
│ │              │  │ 3a·M·F │ │ 2a·P·F │ │ 5a·M·F │          │
│ │ Età          │  │ ●91%   │ │ ●84%   │ │ ●78%   │          │
│ │ Compatibile  │  │ 12 km  │ │ 18 km  │ │ 31 km  │          │
│ │ ☑ bambini    │  └────────┘ └────────┘ └────────┘          │
│ │              │                                             │
│ │ Distanza     │  ┌────────┐ ┌────────┐ ┌────────┐          │
│ │ Milano       │  │  …     │ │  …     │ │  …     │          │
│ │ ◉──── 50 km  │  └────────┘ └────────┘ └────────┘          │
│ └──────────────┘                                             │
│ [Milano ×] [Cane ×] [Piccola, Media ×] [bambini ×]  Azzera   │
└──────────────────────────────────────────────────────────────┘
```

On mobile the filter panel becomes a bottom sheet; the active-filter chip row stays visible above the results.

### Animal profile

```
┌──────────────────────────────────────────────────────────────┐
│  ← Torna ai risultati                                        │
│  ┌────────────────────────────┐  Luna              ♥ Salva   │
│  │                            │  ● Disponibile               │
│  │        [main photo]        │  Femmina · 3 anni · Media    │
│  │                            │  Meticcio · Sterilizzata     │
│  │                            │                              │
│  └────────────────────────────┘  ┌─────────────────────────┐ │
│  [▪][▪][▪][▪][▶ video]           │ ●  91% compatibile      │ │
│                                  │ Luna sembra pensata per │ │
│  La storia di Luna               │ la tua situazione: …    │ │
│  Luna è arrivata da noi          │ ✓ Energia compatibile   │ │
│  nell'inverno del 2024…          │ ✓ Sta bene in appart.   │ │
│                                  │ ✓ Tollera le tue ore    │ │
│  Com'è Luna                      │ ! Non testata coi gatti │ │
│  ┌──────────┬──────────┐         │ [Vedi il dettaglio]     │ │
│  │ Energia  │ ▪▪○○○    │         └─────────────────────────┘ │
│  │ Bambini  │ ✓ Sì     │                                    │
│  │ Cani     │ ✓ Sì     │         ┌─────────────────────────┐ │
│  │ Gatti    │ ? Non    │         │ Canile La Speranza      │ │
│  │          │   testata│         │ Milano (MI) · 12,4 km   │ │
│  │ Sola per │ 6 ore    │         │ [mini map]              │ │
│  └──────────┴──────────┘         │ [Vedi la struttura]     │ │
│                                  └─────────────────────────┘ │
│  In struttura da 214 giorni                                  │
│                                  ┌─────────────────────────┐ │
│  Animali simili                  │  [ Candidati per Luna ] │ │
│  ┌────┐┌────┐┌────┐              │  Gratuito · 4 gg medi   │ │
│  └────┘└────┘└────┘              └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

The apply button is sticky on mobile. The match panel is absent for visitors without a profile and replaced by a quiz invitation.

### Quiz step

```
┌──────────────────────────────────────────────────────────────┐
│  ← Indietro                    Domanda 7 di 14               │
│  ████████████░░░░░░░░░░░░░░                                  │
│                                                              │
│         Quante ore al giorno l'animale                       │
│         resterebbe da solo?                                  │
│                                                              │
│         Rispondi con sincerità: serve a noi per non          │
│         proporti un animale che soffrirebbe.                 │
│                                                              │
│         ┌────────────────────────────────────────┐           │
│         │  0–2 ore                               │           │
│         ├────────────────────────────────────────┤           │
│         │  3–4 ore                               │           │
│         ├────────────────────────────────────────┤           │
│         │  5–6 ore                          ✓    │           │
│         ├────────────────────────────────────────┤           │
│         │  7–8 ore                               │           │
│         ├────────────────────────────────────────┤           │
│         │  Più di 8 ore                          │           │
│         └────────────────────────────────────────┘           │
│                                          [ Continua → ]      │
└──────────────────────────────────────────────────────────────┘
```

One question per screen, options at least 56 px tall, selection advances after a short delay with an undo-by-back always available.

### Shelter dashboard

```
┌──────────────────────────────────────────────────────────────┐
│ Canile La Speranza          Animali Candidature Visite  ⚙︎ 🔔 │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐ │
│ │In cura   ││Disponib. ││Permanenza││Adozioni  ││Candidat. │ │
│ │   64     ││    48    ││  127 gg  ││    7     ││    12    │ │
│ │ 41🐕 23🐈 ││          ││ ▼ 8 gg   ││ ▲ 2      ││ 3 nuove  │ │
│ │  ╱╲╱╲    ││   ╱╲_    ││  ╲╱╲     ││  ╱╲╱     ││ ╱╲       │ │
│ └──────────┘└──────────┘└──────────┘└──────────┘└──────────┘ │
├──────────────────────────────────────────────────────────────┤
│ Richiedono attenzione                     ⓘ Come funziona    │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │[▪] Rocco    418 gg  ●31%  >90 gg                         │ │
│ │    Età >8 anni · Taglia grande · Una sola foto           │ │
│ │    [+ Foto] [+ Video] [Completa profilo] [Affido]     ×  │ │
│ ├──────────────────────────────────────────────────────────┤ │
│ │[▪] Bruno    288 gg  ●44%  >90 gg                         │ │
│ │    Taglia grande · Non compatibile con altri cani        │ │
│ │    [+ Video] [Storia più ricca]                       ×  │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ⓘ Stime da un modello addestrato su dati statunitensi        │
│   2013–2018. Servono a dare priorità, non a decidere.        │
├──────────────────────────────────────────────────────────────┤
│ Ingressi e uscite            │  Distribuzione permanenza     │
│  [line chart]                │   [histogram]                 │
└──────────────────────────────────────────────────────────────┘
```

The caveat under the triage list is permanent and not dismissible.

### Applications queue

```
┌──────────────────────────────────────────────────────────────┐
│ Candidature   [Tutte ▾] [Animale ▾] [Più vecchie ▾]   12     │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ [▪] Luna     PM-7K4Q-2210     Marco R.       ● Nuova     │ │
│ │     Inviata 2 giorni fa · Appartamento · 6 h fuori       │ │
│ │     Prima esperienza · Nessun altro animale              │ │
│ │                                    [Apri]                │ │
│ ├──────────────────────────────────────────────────────────┤ │
│ │ [▪] Bruno    PM-9J2M-2208     Elena V.  ⚠ In attesa 9 gg │ │
│ │     Info richieste il 5/8 · In attesa di risposta        │ │
│ │                                    [Apri]                │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

Applications older than the shelter's target response time carry a warning treatment — the queue's job is to make silence visible.

## 7. Photography and empty states

**Photography guidance** (shipped as in-product help, since photo quality is the single strongest lever a shelter controls):
- Natural daylight, outdoors or by a window; never flash.
- Camera at the animal's eye level, not standing above.
- Eyes in focus and visible; no bars, fences or cage wire between camera and animal where avoidable.
- One animal per photo; a hand or lead in frame is fine and reads as care.
- At least three photos: a portrait, a full body, and one in motion or interacting with a person.
- Aim for 4:3 or square; the grid crops to 4:3.

**Placeholders.** Animals awaiting a photo show a species-appropriate line illustration on `--surface-sunken`, never a stock photo of a different animal, and never a broken image. Publication is blocked until a real photo exists.

**Empty states** always carry an illustration, one sentence of explanation, and one action:

| Context | Message | Action |
|---|---|---|
| No search results | "Nessun animale corrisponde a questi filtri." | "Allarga il raggio a 100 km" |
| Match results too thin | "Solo 3 animali superano la soglia entro 50 km." | "Cerca entro 100 km" |
| No applications | "Nessuna candidatura al momento." | "Controlla che i tuoi animali siano pubblicati" |
| No animals yet (shelter) | "Non hai ancora inserito animali." | "Aggiungi il primo" / "Importa da CSV" |
| Assistant unavailable | "L'assistente non è disponibile in questo momento." | "Consulta le guide" |

## 8. Accessibility

Non-negotiable, WCAG 2.1 AA:

- **Contrast** — 4.5:1 body, 3:1 large text and UI boundaries. Enforced by a CI test over the token pairs in use.
- **Focus** — a visible 2 px `--focus` ring with a 2 px offset on every interactive element. Never removed, never replaced with colour alone.
- **Keyboard** — every flow completable without a mouse, including the gallery, the map (with a list alternative), the quiz, the slot picker and the chat widget. Logical tab order; skip-to-content link.
- **Alt text** — required on animal media in at least one language, with an in-product explanation of why (blind adopters, and search engines). Decorative imagery gets `alt=""`.
- **Forms** — real `<label>` elements, errors bound with `aria-describedby`, errors announced, never colour-only validation.
- **Motion** — `prefers-reduced-motion` removes transitions and disables autoplay entirely.
- **Live regions** — streaming assistant replies, toasts and async results announced politely.
- **Language** — `lang` on `<html>` per locale, and on any inline passage in the other language.
- **Targets** — minimum 44 × 44 px on touch.
- **Zoom** — usable at 200% without horizontal scrolling.
- **Testing** — automated axe checks in CI on every key screen, plus manual keyboard and screen-reader passes each phase.

## 9. Tone of voice

**In both languages:** direct, warm, concrete. Short sentences. Second person singular in Italian (*tu*, not *Lei*) — this is a personal decision, not a bureaucratic one. Never sentimental to the point of manipulation; the animals do not need our adjectives.

| Do | Don't |
|---|---|
| "Luna sta bene con altri cani." | "Luna è un angelo che ama tutti!" |
| "Non è ancora stata testata con i gatti." | (silence) |
| "In struttura da 214 giorni." | "In attesa di un miracolo da 214 giorni." |
| "Stima del modello: probabile attesa oltre 90 giorni." | "Questo cane non verrà adottato." |
| "La struttura risponde in media in 4 giorni." | "Risposta immediata!" |

**Never, in any surface:**
- Words that frame animals as goods — *merce*, *prodotto*, *stock*, *inventario*, *in vendita*, *acquisto*, *cliente* for an adopter.
- Guilt as a lever: "se non lo adotti tu, chi lo farà?" — pressure produces returns.
- Casual reference to euthanasia, or its use as urgency.
- Predictions phrased as certainties, anywhere.
- Breed stereotyping, positive or negative.

**Naming.** *Struttura* or *canile*/*gattile* as appropriate, never *centro di raccolta*. *Adottante* not *cliente*. *Contributo di adozione*, never *prezzo*. In English: *shelter*, *adopter*, *adoption fee*.

**Errors** say what happened and what to do next: "Non siamo riusciti a salvare la candidatura. Riprova tra qualche istante — i dati che hai inserito sono stati conservati." Never "Errore 500".

**AI-generated text** always carries the `AIDisclosure` chip. Users are told plainly when a machine wrote something or estimated something, every time, without exception.
