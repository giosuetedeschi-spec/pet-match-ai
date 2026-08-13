# PetMatch AI — Documentation

Everything below describes a product that has **not been built yet**. These documents are the specification the build will follow. They are written to be implementation-ready: real SQL, real payload shapes, real numbers.

## Start here

**→ [INDEX.md](./INDEX.md)** — the whole set is ~42,000 words. The index carries the product in a paragraph, a question-to-document routing table, every normative constant (matching weights, enums, plan limits, design tokens) in one place, the hard rules that must never be broken, the Austin caveat, and the open questions. Read it first; read a full document only when you are about to build the thing it describes.

## Reading order

| # | Document | What it covers | Read it if you want to know… |
|---|---|---|---|
| — | [**INDEX**](./INDEX.md) | Routing, constants, hard rules, open questions | anything, quickly |
| 01 | [Product Specification](./01-product-spec.md) | Personas, user stories, every screen, the adoption state machine, out-of-scope | *what* we are building |
| 02 | [Technical Architecture](./02-architecture.md) | Stack and rationale, repo layout, auth, tenancy, i18n, media, geo, env vars, Docker | *how* the pieces fit together |
| 03 | [Database Schema](./03-database-schema.md) | Full MySQL DDL, ERD, enums, indexes, seed plan, retention policy | where every piece of data lives |
| 04 | [API Contracts](./04-api-contracts.md) | REST endpoints, payload examples, ML service contract, chatbot tools, webhooks | how the layers talk to each other |
| 05 | [ML Specification](./05-ml-spec.md) | Kaggle dataset, feature engineering, two models, evaluation, honest limitations, retraining | how the predictions are produced and what they mean |
| 06 | [Matching Algorithm](./06-matching-algorithm.md) | The quiz, the scoring weights, worked examples, explanation generation, re-matching | how an adopter is matched to an animal |
| 07 | [Design System](./07-design-system.md) | Visual direction, tokens, components, wireframes, accessibility, tone of voice | what it looks and sounds like |
| 08 | [Roadmap](./08-roadmap.md) | Five build phases with exit criteria, testing strategy, definition of done | in what order it gets built |
| 09 | [Compliance & GDPR](./09-compliance-gdpr.md) | Lawful bases, data inventory, consent points, erasure procedure, microchip/anagrafe | what the law requires of us |
| 10 | [Marketing Plan](./10-marketing-plan.md) | Positioning, competitors, go-to-market, metrics, pricing, projections, naming | how it reaches shelters and adopters — **later** |
| 11 | [Training Workflow](./11-training-workflow.md) | Colab notebook sequence, reproducibility checklist, graduation to scripts | how the models actually get built |
| 12 | [Modelling Approaches](./12-modelling-approaches.md) | Problem formulation, survival analysis recommendation, why not LLM fine-tuning, rejected ideas | which model to build, and why not the others |

If you only read three: **01** (what), **03** (data), **08** (order).

## Decisions already locked in

These were settled during the requirements interview and are treated as fixed by every document here. Changing one means revisiting the documents that depend on it.

| Area | Decision |
|---|---|
| Audience | Adopters **and** shelters, equal weight |
| Tenancy | Multi-shelter platform; adopters search across all shelters |
| Roles | Platform admin · shelter staff · adopter |
| Languages | Italian + English, i18n from day one |
| Species | Dogs and cats only |
| Web stack | Next.js (TypeScript, App Router) + Prisma + MySQL |
| ML stack | Separate Python FastAPI service, scikit-learn |
| UI | Tailwind + shadcn/ui, custom theme, warm & editorial tone |
| ML targets | Adoption probability **and** length of stay |
| Matching | Rule-based weighted scoring + Claude-written explanations, saved adopter profiles |
| Chatbot | Claude + RAG, two personas (public adopter, shelter staff) |
| Adoption journey | Application → shelter review → status tracking → in-app visit scheduling |
| Media | Multiple photos + short video clips per animal |
| Animal record | Identity + behaviour + dated medical history log |
| Search | Filters + distance radius + map view |
| Notifications | In-app + email + WhatsApp |
| Compliance | Microchip / anagrafe fields + GDPR essentials |
| Payments | Stripe — shelter subscriptions and adopter donations, built last |
| Business model | Freemium SaaS for shelters, free forever for adopters, donations accepted |
| Hosting | Portable, Docker Compose, no vendor lock-in |
| Delivery | Phased — a working application at the end of every phase |

## Conventions used across these documents

- **Italian domain terms** are kept where they are the real term of art (*canile*, *gattile*, *anagrafe canina*, *comune*, *CAP*) and glossed on first use.
- SQL, JSON and TypeScript blocks are **illustrative specifications**, not files to copy verbatim. Field names, however, are normative: the schema, API, ML and matching documents all use the same names on purpose.
- Money is always stored and quoted in **cents**, currency EUR.
- Times are stored in **UTC**; the UI renders in `Europe/Rome`.
- "Animal" is used for the record; the UI never refers to animals as inventory, stock, or products. See the tone-of-voice section of the design system.
