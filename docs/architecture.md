# System Architecture

## 1. Logical architecture
```text
Learner / Instructor / Admin browser
              |
              | HTTPS + JSON
              v
React + TypeScript (Vite)
- route/layout layer
- feature modules
- API client and query cache
- accessible UI components
              |
              | /api/v1/*
              v
Django + Django REST Framework
- authentication and authorization
- serializers/input validation
- domain services
- selectors/query layer
- REST views and OpenAPI schema
              |
       +------+------------------+
       |                         |
       v                         v
Neon PostgreSQL             Object storage
- users/course data         - video/audio/PDF
- assessments/progress      - captions/transcripts
- recommendations           - thumbnails
       |
       +---- optional Redis/Celery later
             - email/notifications
             - analytics aggregation
             - media processing coordination
```

## 2. Deployment boundaries
- React is a static frontend deployment or served behind a web proxy.
- Django is deployed as one modular application initially; avoid microservices until operational needs justify them.
- Neon is accessed only by Django. The browser must never receive `DATABASE_URL`.
- Use a separate storage service for large media; save keys/metadata in Neon.
- Keep development, test, and production credentials/data separated.

## 3. Backend domain modules
- `users`: custom user model, roles, profile.
- `courses`: category, course, publication state.
- `content`: modules, lessons, media metadata.
- `enrollments`: course enrollment and ownership rules.
- `progress`: lesson and course progress.
- `assessments`: questions, choices, attempts, server-side scoring.
- `learning`: skills, mastery, recommendations, learning paths.
- `discussions`: threads, replies, moderation.
- `analytics`: event capture and instructor summaries.
- `notifications`: in-app notifications (later phase).

## 4. Request flow
1. React calls an API endpoint using the API client.
2. Django authenticates the caller.
3. Permission checks validate role, course ownership, enrollment, publication state, and resource ownership.
4. Serializer validates the request.
5. A service performs a transaction for multi-step domain changes.
6. Django ORM reads/writes Neon PostgreSQL.
7. A response serializer returns only fields the caller is allowed to see.

## 5. Key domain flows

### Course authoring
Instructor creates draft → adds modules/lessons → attaches media metadata → previews → publishes. Public catalogue returns published courses only.

### Lesson progress
Learner opens enrolled course → starts lesson → client periodically saves media position/progress → completion endpoint records completion → course progress recalculated idempotently.

### Quiz and adaptive recommendation
Server returns questions without correctness flags → learner submits answers → server validates attempt/limits and calculates score → attempt is saved atomically → skill mastery updated → explainable rule-based recommendation generated.

## 6. Security design
- Enforce permissions on every protected endpoint; frontend route guards are convenience only.
- Use Django password hashing and a carefully configured authentication/token strategy.
- Keep secrets in environment variables/secret management.
- Require HTTPS in production; use secure CORS allowlists and appropriate CSRF/token controls.
- Validate file size, MIME type, extension, and ownership; do not trust client-provided MIME alone.
- Rate-limit sensitive endpoints such as login and quiz submission where supported.
- Avoid returning correct quiz answers before submission.
- Do not log passwords, access tokens, refresh tokens, or unnecessary learner information.

## 7. Frontend structure
```text
src/
  app/          router, providers
  components/   reusable UI, forms, media player
  features/
    auth/
    courses/
    authoring/
    learning/
    progress/
    assessments/
    recommendations/
    discussions/
    analytics/
  lib/          API client, query configuration
  types/
```
Use TanStack Query for server state; keep local UI state local. Add a global state library only if a real use case appears.

## 8. Architecture decisions
- Modular monolith: simplest deployment while preserving domain boundaries.
- REST: clear client/server contract and easy testing.
- Neon PostgreSQL: relational constraints and transactions fit course/enrollment/assessment data.
- Rule-based adaptive learning first: explainable, testable, and feasible without training data.
- Object storage for media: separates large-file delivery from transactional data.
