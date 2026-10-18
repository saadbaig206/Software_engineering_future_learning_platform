# Phase 0: Workspace Analysis & Baseline Assessment

**Project:** FutureLearning Learning Engine  
**Course Context:** Complex Computing Problem (CCP) — Software Engineering  
**Date:** 2026-10-17  
**Status:** Completed (Read-Only Analysis)  

---

## 1. Executive Summary

A comprehensive read-only analysis of the `futurelearning_starter` repository was conducted to inventory existing assets, evaluate architectural alignment with project requirements, and identify gaps, conflicts, and technical risks. 

The workspace contains an early-stage starter foundation featuring a custom Django 5.2 + Django REST Framework backend with an active Neon PostgreSQL connection, a preliminary Vite + React + TypeScript frontend, and an indicative set of baseline design documents. However, key infrastructural and architectural capabilities required by the CCP specifications—specifically asynchronous task pipelines (Celery/Redis), S3-compatible media upload abstractions, Next.js App Router architecture, automated CI/CD pipelines, containerization, and formal PERT/CPM project scheduling—are not yet present or require migration.

---

## 2. Inventory of Workspace Artifacts

### 2.1 Root Level
- **`FutureLearning_Design_Baseline.docx` (38.5 KB):** Binary baseline document summarizing the initial academic problem translation, roles (Learner, Instructor, Admin), MVP requirements, architecture overview, and data entities. Fully corresponds to the extracted markdown files in `/docs`.
- **`README.md` (2.8 KB):** Setup instructions and architecture overview. Notes that Django is the sole consumer of Neon, the custom user model must precede initial migrations, and background workers are deferred.
- **Git Repository Status:** The workspace is currently **not initialized as a git repository** (`fatal: not a git repository`).

### 2.2 Documentation (`/docs/`)
Existing documentation provides a structured initial baseline:
- **`requirements.md` (8.8 KB):** Identifies 20 functional requirements (`FR-01` to `FR-20`), 10 non-functional requirements (`NFR-01` to `NFR-10`), 9 business rules (`BR-01` to `BR-09`), and key assumptions. Lacks explicit MoSCoW prioritization, quantifiable NFR targets (e.g., p95 latency percentiles, concurrent user thresholds), and stakeholder-to-requirement mapping required by the CCP prompt.
- **`architecture.md` (4.7 KB):** High-level logical architecture diagram (ASCII), request lifecycle, modular backend domain listing, frontend structure, and security design notes.
- **`data-model.md` (6.3 KB):** Comprehensive logical schema covering 18 entities (`User`, `Category`, `Course`, `Module`, `Lesson`, `MediaAsset`, `Enrollment`, `LessonProgress`, `Assessment`, `Question`, `Choice`, `QuizAttempt`, `Answer`, `AnswerChoice`, `LearningProfile`, `Skill`, `LessonSkill`, `StudentSkill`, `LearningPath`, `LearningPathItem`, `DiscussionThread`, `DiscussionPost`, `Notification`, `LearningEvent`).
- **`erd.mmd` (1.9 KB):** Valid Mermaid ER diagram reflecting core entity relationships.
- **`api-spec.md` (7.0 KB):** Proposed REST endpoints under `/api/v1/` for Auth, Courses, Modules, Lessons, Enrollments, Assessments, Personalization, Discussions, and Analytics.
- **`test-plan.md` (2.5 KB):** Initial high-level test strategy with 20 test scenarios (`TC-001` to `TC-020`). Lacks 1:1 bidirectional requirement traceability, automation mapping, and Playwright E2E coverage.
- **`project-plan.md` (2.8 KB):** Indicative 15-activity WBS (Activities A through O) with single-point estimates. Missing formal PERT three-point calculations, CPM network passes, critical path floats, and reproducible computation scripts.

### 2.3 Backend Service (`/backend/`)
- **Framework & Dependencies:** Python 3.10+, Django 5.2.18, Django REST Framework 3.18.3, `dj-database-url` 2.3.0, `psycopg` 3.3.6 (PostgreSQL binary driver), `django-cors-headers` 4.9.0, `drf-spectacular` 0.30.0.
- **Virtual Environment:** Present at `backend/venv/` with core dependencies installed.
- **Configuration (`backend/config/`):**
  - `settings.py`: Configured to load `.env`. Uses `dj-database-url` to parse `DATABASE_URL` with connection health checks and SSL enabled. Custom user model mapped via `AUTH_USER_MODEL = "users.User"`. Authentication currently defaults to `SessionAuthentication`; SimpleJWT is not yet configured.
  - `urls.py`: Routes admin and drf-spectacular OpenAPI endpoints (`/api/schema/`, `/api/docs/`). Domain API routes are not yet wired.
- **Applications (`backend/apps/`):**
  - `users`: Implements `User` model inheriting from `AbstractUser` with UUID primary key, email as `USERNAME_FIELD`, and `Role` choices (`LEARNER`, `INSTRUCTOR`, `ADMIN`).
  - `courses`, `content`, `enrollments`, `progress`, `assessments`, `learning`, `discussions`: Directory skeletons created; `models.py` files contain `# TODO: implement models from docs/data-model.md`.
- **Database Status:**
  - Active Neon pooled connection string configured in `backend/.env`.
  - `python manage.py check` passes with 0 errors.
  - `python manage.py showmigrations` confirms no migrations have been executed for `apps.users` or domain apps (`contenttypes.0001_initial` is recorded as applied).

### 2.4 Frontend Application (`/frontend/`)
- **Current Technology:** Vite 7.x + React 19.x + TypeScript + React Router DOM (`v6`).
- **Build & Verification Status:** 
  - `package.json` specifies `"dependencies"` with `@vitejs/plugin-react`, `vite`, `typescript`, `react`, `react-dom`, `react-router-dom`.
  - **Issue identified:** `@types/react` and `@types/react-dom` are omitted from `devDependencies`. Executing `npm run build` (`tsc -b && vite build`) fails with TypeScript compilation errors (TS7016, TS7026).
  - Current UI (`App.tsx` and `styles.css`) is a static landing page previewing platform features and roadmap.
- **Framework Conflict vs. CCP Prompt:**
  - Starter uses **Vite + React SPA**.
  - CCP Prompt specifies **Next.js (App Router) + React + TypeScript (strict mode)** with Tailwind or CSS Modules, TanStack Query, and React Hook Form + Zod.

---

## 3. Reusable Assets vs. Identified Gaps

| Component | Existing Starter State | CCP Requirement Specification | Reusability / Action Plan |
|---|---|---|---|
| **Data Model & Schema** | Rich 18-entity specification in `data-model.md` and `erd.mmd`. | Relational schema in Neon supporting multi-format lessons, quiz grading, and adaptive skill graphs. | **Highly Reusable:** Adopt existing entity definitions directly into Phase 2 models and Phase 4 Django apps. |
| **User & RBAC Model** | `apps.users.models.User` with UUID PK and Role enum. | Custom user model with roles (`Learner`, `Instructor`, `Admin`), consent, and RBAC. | **Reusable:** Retain custom model; extend with GDPR consent, email verification, and profile fields before running first migration. |
| **API Contract** | Draft REST endpoints in `docs/api-spec.md`. | Versioned `/api/v1/` endpoints with drf-spectacular OpenAPI generation. | **Reusable:** Refine and formalize into DRF viewsets and serializers. |
| **Authentication** | Django SessionAuthentication configured in settings. | JWT Authentication (`SimpleJWT`) with refresh rotation and secure token handling. | **Gap:** Install `djangorestframework-simplejwt`, update `REST_FRAMEWORK` settings, and implement token lifecycle. |
| **Async Tasks & Caching** | Deferred in starter notes; no Redis or Celery packages installed. | Redis for caching/rate limiting; Celery + Celery Beat for media processing, rollups, and notifications. | **Gap:** Configure Redis connection, Celery worker/beat instances, and task queues in Phase 3. |
| **Media Storage** | Metadata model proposed in `data-model.md`. Large binaries prohibited in DB. | Provider-agnostic S3-compatible storage with direct presigned browser uploads. | **Gap:** Add `django-storages` + `boto3`, implement upload ticket endpoint, and ensure abstraction works across AWS S3/Cloudflare R2/MinIO. |
| **Frontend Framework** | Vite + React SPA (currently failing TypeScript build). | Next.js (App Router) with SSR/CSR, TanStack Query, and React Hook Form. | **Conflict / Gap:** Migrate frontend to Next.js App Router in Phase 3 to satisfy prompt specifications. |
| **Infrastructure & CI** | No `docker-compose.yml`, no `infra/`, no GitHub Actions. | Full docker-compose stack (Django, Next.js, Redis, Celery, Beat), Makefile, CI checks. | **Gap:** Implement in Phase 3. |
| **Project Scheduling** | High-level 15-item single-estimate table. | Formal PERT three-point calculations, CPM forward/backward passes, critical path float, and Python script. | **Gap:** Develop automated Python PERT/CPM calculation script and documentation in Phase 10. |

---

## 4. Key Architectural & Scope Conflicts to Clarify

1. **Frontend Architecture (Vite SPA vs. Next.js App Router):**
   - The repository contains an unconfigured Vite + React app, while the prompt mandates Next.js (App Router). In Phase 3, we recommend scaffolding the Next.js App Router in `/frontend`, preserving existing styling concepts and route layouts.
2. **Database Connection Strategy (Direct vs. Pooled):**
   - The `.env` currently contains a pooled connection endpoint. For Django migrations and schema modifications, Neon requires the direct (non-pooled) endpoint to prevent transaction lock issues with session poolers, while runtime queries utilize the pooled connection. Both connection strings must be supported via environment variables.
3. **Object Storage Provider Selection:**
   - The media architecture requires an S3-compatible service (e.g., AWS S3, Cloudflare R2, MinIO, Wasabi, or Supabase Storage). The abstraction must remain provider-agnostic.
4. **Target Team Size & Working Assumptions:**
   - The academic project parameters require a realistic schedule, budget, and resource plan for a university engineering team. Clarification of target team size (e.g., 3–4 student engineers) is needed to calibrate PERT/CPM estimates.

---

## 5. Technical Risks & Mitigation Strategies

| Risk | Impact | Likelihood | Mitigation Strategy |
|---|---|---|---|
| **Neon Connection Pool Exhaustion** | Backend API 500 errors under concurrent load. | Medium | Utilize Neon pooled endpoint for web queries (`conn_max_age=60`, `conn_health_checks=True`), reserve direct endpoint strictly for migrations, and cache hot reads in Redis. |
| **Large Media Throughput Bottleneck** | Server process starvation and memory exhaustion. | High | Prohibit media streaming through Django. Enforce client-side direct-to-bucket uploads via short-lived presigned URLs. Serve playback assets via CDN. |
| **Early Migration Schema Lock-in** | Costly database refactoring if custom user model or FK constraints are migrated prematurely. | High | Strictly withhold running `makemigrations` and `migrate` until Phase 4, after the custom user model has all necessary fields (consent, active status, roles). |
| **Complexity of Adaptive Engine** | Over-engineering machine learning models exceeding course timeline constraints. | Medium | Implement an explainable, deterministic rule-based knowledge-space model (prerequisite graph + skill mastery scores) encapsulated behind a clean strategy interface. |
| **Accessibility Non-Compliance (WCAG 2.1 AA)** | Penalty against course rubric and inaccessible learner experience. | Medium | Integrate semantic HTML, ARIA attributes, keyboard-trap audits, and automated `axe-core` accessibility assertions directly into component design and CI checks. |

---

## 6. Proposed Target Monorepo Structure

```text
futurelearning/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Linting, type checks, backend tests, frontend tests
│       └── e2e.yml                # Playwright E2E browser tests
├── backend/                       # Django + DRF API-First Monolith
│   ├── apps/
│   │   ├── users/                 # Custom user model, RBAC, auth, profiles
│   │   ├── courses/               # Categories, courses, publishing state
│   │   ├── content/               # Modules, lessons, content blocks, media metadata
│   │   ├── enrollments/           # Course enrollments
│   │   ├── progress/              # Granular lesson progress & resume tracking
│   │   ├── assessments/           # Quizzes, questions, choices, auto-grading
│   │   ├── learning/              # Skills, mastery, adaptive path generator
│   │   ├── discussions/           # Discussion threads, replies, moderation
│   │   ├── analytics/             # Event rollups, instructor/admin metrics
│   │   └── common/                # Shared utilities, base models, storage helpers
│   ├── config/                    # Split settings (base, dev, prod), urls, celery
│   ├── tests/                     # Cross-module integration and API tests
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                      # Next.js (App Router) + TypeScript
│   ├── src/
│   │   ├── app/                   # App router pages (catalog, player, studio, admin)
│   │   ├── components/            # Accessible UI design system & layout components
│   │   ├── features/              # Modular domain features (auth, player, editor)
│   │   ├── lib/                   # API client, TanStack Query hooks, auth storage
│   │   └── types/                 # Shared TypeScript interfaces (OpenAPI generated)
│   ├── public/                    # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
├── infra/                         # Deployment & Local Environment Infrastructure
│   ├── docker-compose.yml         # Django, Next.js, Redis, Celery Worker, Celery Beat
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx/                     # Local reverse proxy configuration
├── docs/                          # Course Deliverables & Living Architectural Docs
│   ├── 00-workspace-analysis.md   # Phase 0 workspace audit
│   ├── 01-requirements.md         # Phase 1 complete requirements spec
│   ├── 02-system-design.md        # Phase 2 high-level architecture & UML models
│   ├── 03-test-plan.md            # Phase 9 test matrix and strategy
│   ├── 04-project-plan.md         # Phase 10 PERT/CPM schedule and risk register
│   ├── 05-validation.md           # Phase 11 validation and rubric mapping
│   ├── decision.md                # Living Architecture Decision Log (D-001+)
│   ├── flow.md                    # Living End-to-End System Flow Document (16 sections)
│   ├── diagrams/                  # Mermaid (.mmd) and PlantUML (.puml) source files
│   └── scripts/                   # Reproducible calculation scripts (pert_cpm.py)
├── Makefile                       # Developer automation shortcuts (test, lint, run)
├── .env.example                   # Root environment template
└── README.md                      # Project overview, architecture, and setup instructions
```

---

## 7. Next Steps

Upon user approval of Phase 0:
1. Proceed to **Phase 1: Requirements Specification**, compiling the complete requirements document (`docs/01-requirements.md`) with explicit MoSCoW prioritization, quantifiable NFR thresholds, acceptance criteria, and justifications aligned with course learning outcomes CLO-2 and CLO-3.
