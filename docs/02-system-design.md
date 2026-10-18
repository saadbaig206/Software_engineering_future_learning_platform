# System Design Specification — FutureLearning Learning Engine

**Document Reference:** `docs/02-system-design.md`  
**Phase:** Phase 2 — System Design  
**Course Context:** Complex Computing Problem (CCP) — Software Engineering (CLO-2, CLO-3)  
**Rubric Mapping:** C1 Clarity of Objective, C2 Innovation, C3 Modularity, C4 Validation, C5 Planning  
**Status:** Approved Architecture Baseline  

---

## 1. Executive Architectural Summary

The **FutureLearning Learning Engine** is architectured as a decoupled, **Layered Modular Monolith** paired with an asynchronous task execution tier and a high-performance presentation client. The system bridges enterprise scalability and pedagogical adaptability while respecting strict project constraints: a 4-person university engineering team, a 12-week delivery schedule, zero budget for proprietary microservices infrastructure, and mandatory universal accessibility (**WCAG 2.1 Level AA**).

```text
+-------------------------------------------------------------------------------------------------+
|                                     CLIENT PRESENTATION TIER                                     |
|               Next.js App Router (React, TypeScript Strict, Tailwind CSS, TanStack Query)       |
+------------------------------------------------+------------------------------------------------+
                                                 |
                                     HTTPS REST  |  (/api/v1/*)
                                                 v
+-------------------------------------------------------------------------------------------------+
|                                 MODULAR MONOLITH CORE (Django / DRF)                            |
|  +------------------+  +------------------+  +--------------------+  +-----------------------+  |
|  | apps.users       |  | apps.courses     |  | apps.content       |  | apps.enrollments      |  |
|  +------------------+  +------------------+  +--------------------+  +-----------------------+  |
|  +------------------+  +------------------+  +--------------------+  +-----------------------+  |
|  | apps.progress    |  | apps.assessments |  | apps.learning      |  | apps.discussions      |  |
|  +------------------+  +------------------+  +--------------------+  +-----------------------+  |
+------------------------+------------------------------------+-----------------------------------+
                         |                                    |
          Transactional  |                      Cache-Aside   |  Broker & Job Queues
          PostgreSQL     v                      In-Memory     v
+------------------------------------+  +---------------------------------------------------------+
|     Neon Serverless PostgreSQL     |  |                   Redis Memory Store                    |
| (Pooled App Queries / Direct DDL)  |  |      (Rate Limits, Cache, Celery Task Message Broker)    |
+------------------------------------+  +----------------------------+----------------------------+
                                                                     |
                                                        Worker Tasks |  (Media, Analytics, Path)
                                                                     v
+------------------------------------+  +---------------------------------------------------------+
|    S3-Compatible Object Storage    |<--|            Celery & Celery Beat Worker Fleet            |
| (Presigned Direct Binary Uploads)  |  |           (Asynchronous Background Task Processing)     |
+------------------------------------+  +---------------------------------------------------------+
```

---

## 2. High-Level Architecture & Architectural Justification

### 2.1 Architectural Paradigm: Layered Modular Monolith
The core backend is implemented as a single deployable unit divided internally into bounded domain modules (`apps/users`, `apps/courses`, `apps/content`, `apps/enrollments`, `apps/progress`, `apps/assessments`, `apps/learning`, `apps/discussions`, `apps/analytics`). Each domain owns its models, service layer, selectors, serializers, and REST viewsets.

Inter-module communication follows strict software engineering rules:
1. **Direct Foreign Keys are permitted for relational referential integrity** within the single relational database (Neon PostgreSQL).
2. **Business logic transitions cross boundaries via Public Service Selectors** rather than reaching directly into another module's internal state.
3. **High-load side effects are decoupled via asynchronous Celery tasks** (e.g., assessment submissions trigger asynchronous skill mastery recalculation).

### 2.2 Justification vs. Distributed Microservices
In accordance with course rubric criteria **C3 (Modularity)** and **C5 (Planning)**, the engineering team formally evaluated and rejected a distributed microservices architecture ([`D-007`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-007-modular-monolith-architecture-over-microservices)):

| Architectural Dimension | Distributed Microservices | Layered Modular Monolith (Chosen) | Academic & Operational Rationale |
|---|---|---|---|
| **Transactional Integrity** | Requires distributed two-phase commit or Saga pattern across network boundaries. | ACID transactions natively enforced within Neon PostgreSQL. | Critical for enrollment ledgers, quiz grading, and progress state consistency. |
| **Operational & DevOps Overhead** | Requires service mesh (Envoy/Consul), multiple CI/CD pipelines, distributed tracing, and independent container clusters. | Single container deployment for API, single background worker image, unified CI/CD. | A 4-person student team cannot expend 40% of schedule on distributed infrastructure plumbing. |
| **Network Latency & Performance** | Intra-service network serialization (gRPC/HTTP JSON) adds 20–80 ms per hop. | In-process Python method invocation takes $< 0.1\text{ ms}$; zero internal network hops. | Guarantees meeting $p95 < 300\text{ ms}$ response targets (`NFR-PERF-01`). |
| **Extensibility & Future Decomposition** | Premature boundary freezing leads to distributed monolith antipattern. | Clean module boundaries (`apps/*`) allow future extraction of individual microservices if team size scales. | Preserves maximum architectural agility with zero immediate penalty. |

---

## 3. Major Components & Boundary Interactions

```mermaid
flowchart TB
    subgraph Client [Next.js App Router Client]
        LearnerClient["Learner Experience\n(Catalog, Player, Dashboard)"]
        AuthorStudio["Content Designer Studio\n(WYSIWYG, Media Uploader, Quiz Editor)"]
    end

    subgraph CoreServices [Django Modular Domain Boundary]
        AuthModule["1. Auth & RBAC\n(JWT, 5-Tier Roles, Permissions)"]
        CourseModule["2. Course & Content\n(Courses, Modules, Lessons, ContentBlocks)"]
        MediaModule["3. Media Pipeline\n(Presigned Ticket Issuance, Validation)"]
        EnrollModule["4. Enrollment Service\n(Course Registration, Invariants)"]
        ProgressModule["5. Progress Tracking\n(Debounced Heartbeat, Completion Logic)"]
        AssessmentModule["6. Assessment Engine\n(Server-Side Grading, Attempt Limits)"]
        AdaptiveModule["7. Adaptive Engine\n(Skill Graph, KST Recommender)"]
        ForumModule["8. Discussion & Moderation\n(Threads, Posts, Flagging, Moderation Queue)"]
        AnalyticsModule["9. Telemetry & Analytics\n(Rollups, Funnel Analysis, Telemetry)"]
        NotifyModule["10. Notifications\n(In-App Event Dispatcher)"]
    end

    LearnerClient --> AuthModule
    LearnerClient --> CourseModule
    LearnerClient --> EnrollModule
    LearnerClient --> ProgressModule
    LearnerClient --> AssessmentModule
    LearnerClient --> AdaptiveModule
    LearnerClient --> ForumModule

    AuthorStudio --> AuthModule
    AuthorStudio --> CourseModule
    AuthorStudio --> MediaModule
    AuthorStudio --> AssessmentModule
    AuthorStudio --> AnalyticsModule

    %% Internal Module Interactions
    EnrollModule --> CourseModule
    ProgressModule --> EnrollModule
    ProgressModule --> CourseModule
    AssessmentModule --> ProgressModule
    AssessmentModule --> AdaptiveModule
    AdaptiveModule --> CourseModule
    ForumModule --> CourseModule
    AnalyticsModule --> ProgressModule
    AnalyticsModule --> AssessmentModule
    AuthModule -.-> NotifyModule
    ForumModule -.-> NotifyModule
```

1. **Auth & RBAC Module (`apps.users`):** Authenticates users via SimpleJWT, issues rotating refresh tokens, enforces 5-tier role permissions, and records GDPR consent logs (`FR-AUTH-01`–`05`).
2. **Course & Content Management (`apps.courses`, `apps.content`):** Manages the 4-level pedagogical hierarchy (`Course` > `Module` > `Lesson` > `ContentBlock`), supporting polymorphic block types and draft/publish workflows (`FR-CRS-01`–`07`).
3. **Media Pipeline (`apps.content.media`):** Issues presigned S3 upload URLs to the browser and coordinates asynchronous Celery validation, thumbnail generation, and closed-caption ingestion (`FR-MED-01`–`05`).
4. **Enrollment Service (`apps.enrollments`):** Enforces single-enrollment invariants and initializes blank progress ledgers upon course entry (`FR-CRS-03`).
5. **Progress Tracking Engine (`apps.progress`):** Consumes debounced 10-second client playback heartbeats, updates lesson completion percent, and idempotently calculates overall course completion (`FR-TRK-01`–`04`).
6. **Assessment & Grading Engine (`apps.assessments`):** Conceals correct answer keys from browsers, validates attempt limits (`max_attempts`), computes partial credit on multi-select questions, and records atomic grades (`FR-ASM-01`–`06`).
7. **Adaptive Personalization Engine (`apps.learning`):** Implements Knowledge-Space Theory over a directed skill graph, continuously updating student mastery vectors and executing branching logic (< 70% remedial, $\ge 85\%$ advanced) (`FR-PER-01`–`05`).
8. **Discussion & Moderation (`apps.discussions`):** Contextual course/lesson forums, nested replies, offensive content flagging, and moderator queue management (`FR-DIS-01`–`05`).
9. **Telemetry & Analytics (`apps.analytics`):** Computes background rollups for instructor dashboards, identifying lesson drop-off bottlenecks and question discrimination indices (`FR-ANL-01`–`04`).
10. **Notification Dispatcher (`apps.notifications`):** Queues asynchronous in-app alerts and digest notifications for replies, grades, and enrollments (`FR-NOT-01`–`03`).

---

## 4. Formal UML Architectural Models

All UML models are maintained as version-controlled Mermaid source files in [`docs/diagrams/`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams) and embedded below for complete traceability.

### 4.1 System Use Case Model
- **Source File:** [`docs/diagrams/use-case.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/use-case.mmd)
- **Description:** Depicts the interaction boundaries between the five platform actors and the core functional modules.

```mermaid
flowchart LR
    subgraph Actors [System Actors]
        direction TB
        G["Guest"]
        L["Learner"]
        I["Instructor / Designer"]
        M["Moderator"]
        A["Administrator"]
    end

    subgraph AuthApp [Authentication & Governance]
        UC_Reg(["Register & Verify Email\n(FR-AUTH-01)"])
        UC_Login(["Login & Refresh Tokens\n(FR-AUTH-03)"])
        UC_UserMgmt(["Manage Users & Roles\n(FR-ADM-01)"])
        UC_GDPR(["GDPR Consent & Data Export\n(FR-AUTH-05, NFR-PRIV-01)"])
    end

    subgraph CourseApp [Course & Content Management]
        UC_Browse(["Browse Catalog & Syllabi\n(FR-CRS-01, FR-CRS-02)"])
        UC_Enroll(["Enroll in Course\n(FR-CRS-03)"])
        UC_Author(["Author Modules & Lessons\n(FR-CRS-04, FR-CRS-05)"])
        UC_Publish(["Course Publish Lifecycle\n(FR-CRS-06, FR-CRS-07)"])
        UC_MediaUpload(["Direct Media Upload\n(FR-MED-01, FR-MED-02)"])
    end

    subgraph LearnApp [Learning, Progress & Adaptive]
        UC_Learn(["Study Multi-Format Lessons\n(FR-CRS-05, FR-MED-03)"])
        UC_Progress(["Track Resume & Completion\n(FR-TRK-01, FR-TRK-02)"])
        UC_Adaptive(["Receive Adaptive Path\n(FR-PER-03, FR-PER-04)"])
        UC_Quiz(["Take Quizzes & View Feedback\n(FR-ASM-01 - FR-ASM-04)"])
        UC_Sim(["Engage in Simulations\n(FR-SIM-01 - FR-SIM-03)"])
    end

    subgraph SocialApp [Community & Analytics]
        UC_Forum(["Post & Reply in Forums\n(FR-DIS-01, FR-DIS-02)"])
        UC_Moderate(["Moderate Flagged Posts\n(FR-DIS-04, FR-DIS-05)"])
        UC_Analytics(["Review Course Analytics\n(FR-ANL-01 - FR-ANL-03)"])
    end

    %% Actor Connections
    G --> UC_Browse
    G --> UC_Reg
    G --> UC_Login

    L --> UC_Enroll
    L --> UC_Learn
    L --> UC_Progress
    L --> UC_Quiz
    L --> UC_Sim
    L --> UC_Adaptive
    L --> UC_Forum
    L --> UC_GDPR

    I --> UC_Author
    I --> UC_Publish
    I --> UC_MediaUpload
    I --> UC_Analytics
    I --> UC_Forum

    M --> UC_Moderate
    M --> UC_Forum

    A --> UC_UserMgmt
    A --> UC_Publish
    A --> UC_Moderate
    A --> UC_GDPR
```

---

### 4.2 Component Architecture Model
- **Source File:** [`docs/diagrams/component-architecture.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/component-architecture.mmd)
- **Description:** Details internal component contracts across Presentation, Gateway, Service, Async Worker, and Data Persistence tiers.

```mermaid
flowchart TB
    subgraph ClientTier [Frontend Presentation Layer - Next.js App Router]
        direction TB
        CatalogUI["Catalog & Discovery UI\n(FR-CRS-01, FR-CRS-02)"]
        PlayerUI["Multi-Format Course Player\n(FR-CRS-05, FR-MED-03, FR-SIM-01)"]
        StudioUI["Content Designer Studio\n(FR-CRS-04, FR-MED-01, FR-USAB-01)"]
        DashboardUI["Student & Analytics Dashboard\n(FR-TRK-03, FR-ANL-01)"]
        ForumUI["Community Discussion UI\n(FR-DIS-01, FR-DIS-02)"]
        APIClient["Typed OpenAPI Client\n(TanStack Query + Axios)"]
        
        CatalogUI --> APIClient
        PlayerUI --> APIClient
        StudioUI --> APIClient
        DashboardUI --> APIClient
        ForumUI --> APIClient
    end

    subgraph GatewayTier [API Gateway & Security Boundary]
        AuthMiddleware["JWT Authentication &\nRBAC Permission Guard\n(FR-AUTH-02, FR-AUTH-03)"]
        RateLimiter["Redis-Backed Rate Limiter\n(NFR-SEC-01)"]
    end

    subgraph ServiceTier [Django Modular Core Domain Services]
        direction TB
        AuthService["Auth & User Service\n(apps.users)"]
        CourseService["Course & Content Service\n(apps.courses, apps.content)"]
        MediaService["Media Ingestion Service\n(apps.content.media)"]
        EnrollmentService["Enrollment Service\n(apps.enrollments)"]
        ProgressService["Progress Tracking Engine\n(apps.progress)"]
        AssessmentService["Assessment & Grading Engine\n(apps.assessments)"]
        AdaptiveEngine["Adaptive Learning Engine\n(apps.learning)"]
        DiscussionService["Forum & Moderation Service\n(apps.discussions)"]
        AnalyticsService["Telemetry & Analytics Service\n(apps.analytics)"]
        NotificationService["Notification Dispatcher\n(apps.notifications)"]

        EnrollmentService --> CourseService
        ProgressService --> EnrollmentService
        ProgressService --> CourseService
        AssessmentService --> ProgressService
        AssessmentService --> AdaptiveEngine
        AdaptiveEngine --> CourseService
        DiscussionService --> CourseService
        AnalyticsService --> ProgressService
        AnalyticsService --> AssessmentService
    end

    subgraph AsyncTier [Asynchronous Task Worker Tier - Celery & Celery Beat]
        CeleryWorker["Celery Background Worker"]
        CeleryBeat["Celery Beat Scheduler"]
        
        MediaWorkerTask["Media Processing & Validation\n(FR-MED-02)"]
        AdaptiveTask["Mastery & Path Recomputation\n(FR-PER-02, FR-PER-04)"]
        AnalyticsTask["Periodic Metric Rollups\n(FR-ANL-01 - FR-ANL-04)"]
        NotifyTask["Async Notification Dispatch\n(FR-NOT-01)"]

        CeleryWorker --> MediaWorkerTask
        CeleryWorker --> AdaptiveTask
        CeleryWorker --> NotifyTask
        CeleryBeat --> AnalyticsTask
    end

    subgraph DataTier [Storage & Persistence Tier]
        NeonDB[("Neon Serverless PostgreSQL\n(Relational Truth, Schema & Ledgers)")]
        RedisCache[("Redis Memory Store\n(Cache, Sessions, Rate Limits, Queues)")]
        ObjectStore[("S3-Compatible Object Storage\n(Direct Video, Audio, Docs, Thumbs)")]
        CDN["Global Content Delivery Network"]
    end

    APIClient -- "HTTPS /api/v1/*" --> AuthMiddleware
    AuthMiddleware --> RateLimiter
    RateLimiter --> ServiceTier

    StudioUI -- "Direct Presigned Upload" --> ObjectStore
    PlayerUI -- "Stream Media" --> CDN
    CDN --> ObjectStore

    ServiceTier --> NeonDB
    ServiceTier --> RedisCache
    ServiceTier -- "Enqueue Async Jobs" --> RedisCache
    RedisCache -- "Consume Queues" --> CeleryWorker

    MediaWorkerTask --> ObjectStore
    MediaWorkerTask --> NeonDB
    AdaptiveTask --> NeonDB
    AdaptiveTask --> RedisCache
    AnalyticsTask --> NeonDB
    NotifyTask --> NeonDB
```

---

### 4.3 Class & Domain Model
- **Source File:** [`docs/diagrams/class-domain-model.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/class-domain-model.mmd)
- **Description:** Object-oriented domain model illustrating entities, field types, cardinalities, and encapsulation methods.

```mermaid
classDiagram
    direction TB

    class User {
        +UUID id
        +String email
        +String role
        +Boolean is_active
        +DateTime date_joined
        +register()
        +has_role(role)
    }

    class Category {
        +UUID id
        +String name
        +String slug
        +String description
    }

    class Course {
        +UUID id
        +UUID instructor_id
        +UUID category_id
        +String title
        +String slug
        +String difficulty
        +String status
        +Int estimated_duration_minutes
        +publish()
        +archive()
    }

    class Module {
        +UUID id
        +UUID course_id
        +String title
        +Int position
    }

    class Lesson {
        +UUID id
        +UUID module_id
        +String title
        +Int position
        +Boolean is_required
        +Boolean is_preview
        +Boolean is_published
    }

    class ContentBlock {
        +UUID id
        +UUID lesson_id
        +String block_type
        +Int position
        +JSON content_payload
        +UUID media_asset_id
    }

    class MediaAsset {
        +UUID id
        +UUID uploaded_by_id
        +String storage_key
        +String original_filename
        +String mime_type
        +Int size_bytes
        +Int duration_seconds
        +String transcript_url
        +String captions_url
    }

    class Enrollment {
        +UUID id
        +UUID learner_id
        +UUID course_id
        +String status
        +DateTime enrolled_at
        +DateTime completed_at
        +calculate_progress()
    }

    class LessonProgress {
        +UUID id
        +UUID enrollment_id
        +UUID lesson_id
        +String status
        +Int completion_percent
        +Int last_position_seconds
        +mark_complete()
    }

    class Assessment {
        +UUID id
        +UUID lesson_id
        +String title
        +Int passing_score_percent
        +Int time_limit_seconds
        +Int max_attempts
        +Boolean is_published
    }

    class Question {
        +UUID id
        +UUID assessment_id
        +String question_type
        +String prompt
        +Int points
        +Int position
        +String explanation
    }

    class Choice {
        +UUID id
        +UUID question_id
        +String text
        +Int position
        +Boolean is_correct
    }

    class QuizAttempt {
        +UUID id
        +UUID assessment_id
        +UUID enrollment_id
        +Int attempt_number
        +String status
        +Int score_percent
        +Boolean passed
        +submit_and_grade()
    }

    class Answer {
        +UUID id
        +UUID attempt_id
        +UUID question_id
        +Int awarded_points
        +Boolean is_correct
    }

    class Skill {
        +UUID id
        +String name
        +String slug
        +String description
    }

    class LessonSkill {
        +UUID id
        +UUID lesson_id
        +UUID skill_id
        +Float contribution_weight
    }

    class StudentSkill {
        +UUID id
        +UUID learner_id
        +UUID skill_id
        +Int mastery_score
        +update_mastery()
    }

    class LearningPath {
        +UUID id
        +UUID learner_id
        +UUID course_id
        +String status
        +DateTime generated_at
        +regenerate()
    }

    class LearningPathItem {
        +UUID id
        +UUID learning_path_id
        +UUID lesson_id
        +Int position
        +String reason
        +String status
    }

    class DiscussionThread {
        +UUID id
        +UUID course_id
        +UUID lesson_id
        +UUID author_id
        +String title
        +String body
        +String status
    }

    class DiscussionPost {
        +UUID id
        +UUID thread_id
        +UUID author_id
        +UUID parent_id
        +String body
        +String status
    }

    %% Relationships
    User "1" --> "*" Course : instructs
    User "1" --> "*" Enrollment : enrolls
    User "1" --> "*" StudentSkill : develops
    User "1" --> "*" LearningPath : receives
    User "1" --> "*" DiscussionPost : writes

    Category "1" --> "*" Course : groups
    Course "1" *-- "*" Module : contains
    Module "1" *-- "*" Lesson : contains
    Lesson "1" *-- "*" ContentBlock : contains
    ContentBlock "0..1" --> "0..1" MediaAsset : references

    Enrollment "1" *-- "*" LessonProgress : tracks
    Lesson "1" --> "*" LessonProgress : recorded_in

    Lesson "1" *-- "0..1" Assessment : assesses
    Assessment "1" *-- "*" Question : contains
    Question "1" *-- "*" Choice : offers
    Enrollment "1" --> "*" QuizAttempt : attempts
    Assessment "1" --> "*" QuizAttempt : evaluates
    QuizAttempt "1" *-- "*" Answer : contains

    Lesson "1" --> "*" LessonSkill : links
    Skill "1" --> "*" LessonSkill : maps_to
    Skill "1" --> "*" StudentSkill : measures

    LearningPath "1" *-- "*" LearningPathItem : orders
    Lesson "1" --> "*" LearningPathItem : targets

    Course "1" --> "*" DiscussionThread : hosts
    DiscussionThread "1" *-- "*" DiscussionPost : contains
    DiscussionPost "0..1" --> "*" DiscussionPost : replies_to
```

---

### 4.4 Relational Database Entity-Relationship Diagram (ERD)
- **Source File:** [`docs/diagrams/erd.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/erd.mmd)
- **Description:** Complete relational schema deployed to Neon PostgreSQL, showing composite unique keys, primary keys, and foreign keys.

```mermaid
erDiagram
    USER ||--o{ COURSE : instructs
    CATEGORY o|--o{ COURSE : categorizes
    COURSE ||--o{ MODULE : contains
    MODULE ||--o{ LESSON : contains
    LESSON ||--o{ CONTENT_BLOCK : contains
    USER ||--o{ ENROLLMENT : has
    COURSE ||--o{ ENROLLMENT : receives
    ENROLLMENT ||--o{ LESSON_PROGRESS : tracks
    LESSON ||--o{ LESSON_PROGRESS : has
    CONTENT_BLOCK o|--o| MEDIA_ASSET : references
    LESSON ||--o| ASSESSMENT : may_have
    ASSESSMENT ||--o{ QUESTION : contains
    QUESTION ||--o{ CHOICE : offers
    ENROLLMENT ||--o{ QUIZ_ATTEMPT : makes
    ASSESSMENT ||--o{ QUIZ_ATTEMPT : records
    QUIZ_ATTEMPT ||--o{ ANSWER : contains
    USER ||--o{ STUDENT_SKILL : develops
    SKILL ||--o{ STUDENT_SKILL : measured_as
    LESSON ||--o{ LESSON_SKILL : contributes
    SKILL ||--o{ LESSON_SKILL : maps_to
    USER ||--o{ LEARNING_PATH : receives
    LEARNING_PATH ||--o{ LEARNING_PATH_ITEM : contains
    LESSON ||--o{ LEARNING_PATH_ITEM : recommends
    COURSE ||--o{ DISCUSSION_THREAD : hosts
    DISCUSSION_THREAD ||--o{ DISCUSSION_POST : contains
    USER ||--o{ DISCUSSION_POST : writes

    USER {
      uuid id PK
      string email UK
      string password_hash
      string role
      boolean is_active
      timestamp date_joined
    }
    COURSE {
      uuid id PK
      uuid instructor_id FK
      uuid category_id FK
      string title
      string slug UK
      string difficulty
      string status
      int estimated_duration_minutes
    }
    MODULE {
      uuid id PK
      uuid course_id FK
      string title
      int position
    }
    LESSON {
      uuid id PK
      uuid module_id FK
      string title
      int position
      boolean is_required
      boolean is_preview
    }
    CONTENT_BLOCK {
      uuid id PK
      uuid lesson_id FK
      string block_type
      int position
      jsonb content_payload
      uuid media_asset_id FK
    }
    ENROLLMENT {
      uuid id PK
      uuid learner_id FK
      uuid course_id FK
      string status
      timestamp enrolled_at
      timestamp completed_at
    }
    LESSON_PROGRESS {
      uuid id PK
      uuid enrollment_id FK
      uuid lesson_id FK
      string status
      int completion_percent
      int last_position_seconds
    }
    ASSESSMENT {
      uuid id PK
      uuid lesson_id FK
      string title
      int passing_score_percent
      int time_limit_seconds
      int max_attempts
    }
    QUIZ_ATTEMPT {
      uuid id PK
      uuid assessment_id FK
      uuid enrollment_id FK
      int attempt_number
      string status
      int score_percent
      boolean passed
    }
```

---

### 4.5 Sequence Diagrams for Key End-to-End Scenarios

#### Scenario 1: Authentication & JWT Lifecycle
- **Source File:** [`docs/diagrams/seq-login.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/seq-login.mmd)

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Learner Browser
    participant Gateway as Django API Gateway
    participant SimpleJWT as SimpleJWT Auth Middleware
    participant Redis as Redis Cache / Blacklist
    participant DB as Neon PostgreSQL (Users)

    Learner->>Gateway: POST /api/v1/auth/login/ {email, password}
    Gateway->>DB: Query User by email (normalized lowercase)
    DB-->>Gateway: User Record (password hash, role, is_active)
    
    alt Invalid Credentials or Inactive User
        Gateway-->>Learner: HTTP 401 Unauthorized {"detail": "Invalid credentials"}
    else Valid Credentials
        Gateway->>SimpleJWT: Generate Token Pair (UUID, email, role)
        SimpleJWT-->>Gateway: Access Token (15m), Refresh Token (7d)
        Gateway->>Redis: Record Active Session Metadata
        Gateway-->>Learner: HTTP 200 OK {access_token, refresh_token, user: {id, email, role}}
    end

    opt Token Refresh Lifecycle (Subsequent Request)
        Learner->>Gateway: POST /api/v1/auth/refresh/ {refresh_token}
        Gateway->>Redis: Check if refresh_token is blacklisted
        alt Token Blacklisted
            Redis-->>Gateway: Blacklisted
            Gateway-->>Learner: HTTP 401 Unauthorized {"detail": "Token revoked"}
        else Token Valid
            Gateway->>SimpleJWT: Rotate Refresh Token
            SimpleJWT->>Redis: Blacklist old refresh token
            SimpleJWT-->>Gateway: New Access Token + New Refresh Token
            Gateway-->>Learner: HTTP 200 OK {access_token, refresh_token}
        end
    end
```

#### Scenario 2: Presigned Media Upload & Asynchronous Ingestion
- **Source File:** [`docs/diagrams/seq-upload-content.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/seq-upload-content.mmd)

```mermaid
sequenceDiagram
    autonumber
    actor Designer as Content Designer Studio
    participant API as Django API Service
    participant S3 as S3-Compatible Object Storage
    participant Celery as Celery Async Queue (Redis)
    participant Worker as Celery Background Worker
    participant DB as Neon PostgreSQL (MediaAsset)

    Designer->>API: POST /api/v1/lessons/{id}/media-upload-url/ {filename, size, mime_type}
    API->>API: Validate Designer Permissions & Allowed MIME Types
    API->>S3: Generate Presigned PUT URL (15-min expiry, exact Content-Type)
    S3-->>API: Presigned URL + Storage Key
    API-->>Designer: HTTP 200 OK {upload_url, storage_key}

    Designer->>S3: PUT binary file directly to S3 Bucket with Progress Telemetry
    S3-->>Designer: HTTP 200 OK (Upload Complete)

    Designer->>API: POST /api/v1/media-assets/confirm/ {storage_key, original_name}
    API->>DB: Create MediaAsset (status=PROCESSING, size, storage_key)
    DB-->>API: MediaAsset Record Created
    API->>Celery: Enqueue task: process_media_asset(media_asset_id)
    API-->>Designer: HTTP 202 Accepted {media_asset_id, status: "PROCESSING"}

    Worker->>Celery: Dequeue process_media_asset task
    Worker->>S3: Inspect Magic Bytes & Verify Antivirus Hash
    alt Magic Bytes Mismatch or Malicious Payload
        Worker->>S3: Delete Object from Bucket
        Worker->>DB: Update MediaAsset (status=REJECTED)
    else File Valid
        Worker->>Worker: Extract Duration & Generate Video Thumbnail / Audio Waveform
        Worker->>S3: Store Thumbnail Image & Derived Assets
        Worker->>DB: Update MediaAsset (status=READY, duration_seconds, thumbnail_key)
    end
```

#### Scenario 3: Assessment Scoring & Adaptive Pathway Calibration
- **Source File:** [`docs/diagrams/seq-quiz-adaptive.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/seq-quiz-adaptive.mmd)

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Learner Client
    participant API as Django Assessment Service
    participant DB as Neon PostgreSQL
    participant Adaptive as Adaptive Learning Engine
    participant Redis as Redis Cache

    Learner->>API: GET /api/v1/assessments/{id}/
    API->>DB: Query Assessment, Questions, Choices (is_correct omitted)
    DB-->>API: Assessment Data (Learner-Safe Payload)
    API-->>Learner: HTTP 200 OK (Questions, Choices, Time Limit, Max Attempts)

    Learner->>API: POST /api/v1/assessments/{id}/attempts/
    API->>DB: Verify active enrollment & count past attempts < max_attempts
    DB-->>API: Attempt Allowed
    API->>DB: Create QuizAttempt (attempt_number=n, status=IN_PROGRESS)
    API-->>Learner: HTTP 201 Created {attempt_id, started_at}

    Learner->>API: POST /api/v1/attempts/{id}/submit/ {answers: [{question_id, choices}]}
    API->>DB: Fetch Question Keys & Choice.is_correct (atomic lock)
    API->>API: Calculate Score: Points Earned / Total Points = score_percent
    API->>DB: Update QuizAttempt (status=GRADED, score_percent, passed)

    API->>Adaptive: update_learner_skills(learner_id, attempt_id)
    Adaptive->>DB: Fetch LessonSkills associated with tested questions
    Adaptive->>Adaptive: Compute updated mastery scores (Bayesian / Exponential moving avg)
    Adaptive->>DB: Upsert StudentSkill records

    Adaptive->>Adaptive: evaluate_adaptive_branch(score_percent)
    alt score_percent < 70% (Remedial Branch)
        Adaptive->>DB: Insert Remedial Prerequisite Lessons into LearningPathItem
    else score_percent >= 85% (Advanced Branch)
        Adaptive->>DB: Insert Advanced Enrichment Lessons into LearningPathItem
    else Standard Passing (70% - 84%)
        Adaptive->>DB: Progress to Next Sequential Curriculum Unit
    end

    Adaptive->>Redis: Invalidate cached learning path for learner
    API-->>Learner: HTTP 200 OK {score_percent, passed, explanations, adaptive_recommendation}
```

#### Scenario 4: Debounced Progress Heartbeat & Course Completion
- **Source File:** [`docs/diagrams/seq-progress-sync.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/seq-progress-sync.mmd)

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Learner Media Player
    participant API as Django Progress Service
    participant DB as Neon PostgreSQL (Progress & Enrollment)
    participant Redis as Redis Cache

    Note over Learner: Video / Audio playback actively streaming
    loop Every 10 Seconds (Debounced Client Heartbeat)
        Learner->>API: PATCH /api/v1/lessons/{id}/progress/ {last_position_seconds: 145, completion_percent: 65}
        API->>DB: Upsert LessonProgress (enrollment_id, lesson_id, position, percent)
        DB-->>API: LessonProgress Record Updated
        API-->>Learner: HTTP 200 OK {status: "IN_PROGRESS"}
    end

    Learner->>API: POST /api/v1/lessons/{id}/complete/
    API->>DB: Fetch Lesson.is_required status
    API->>DB: Update LessonProgress (status=COMPLETED, completion_percent=100)
    
    API->>DB: Count total required lessons vs completed required lessons in Course
    alt All Required Lessons Completed
        API->>DB: Update Enrollment (status=COMPLETED, completed_at=NOW())
        API->>Redis: Invalidate learner course progress cache
        API-->>Learner: HTTP 200 OK {course_status: "COMPLETED", progress_percent: 100}
    else Incomplete Required Lessons Remaining
        API->>DB: Update Enrollment (progress_percent = completed / total * 100)
        API-->>Learner: HTTP 200 OK {course_status: "ACTIVE", progress_percent: 75}
    end
```

---

### 4.6 State Machine Models

#### State Machine 1: Course Authoring & Publishing Lifecycle
- **Source File:** [`docs/diagrams/state-course-publish.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/state-course-publish.mmd)

```mermaid
stateDiagram-v2
    [*] --> Draft : Course Created by Instructor

    state Draft {
        [*] --> EditingContent
        EditingContent --> AddingModulesLessons : Add Structure
        AddingModulesLessons --> UploadingMedia : Direct Presigned Upload
        UploadingMedia --> PreviewingDraft : Review in Studio
        PreviewingDraft --> EditingContent : Revise Content
    }

    Draft --> InReview : Instructor Submits for Verification\n(Validates >=1 module, >=1 lesson)
    
    InReview --> Draft : Rejection / Changes Requested\n(Feedback provided)
    
    InReview --> Published : Admin / Lead Approval\n(Invalidates Catalog Cache)

    state Published {
        [*] --> LiveToLearners
        LiveToLearners --> CreatingMinorRevision : Non-breaking edit\n(Auto-versions snapshot)
        CreatingMinorRevision --> LiveToLearners : Save revision
    }

    Published --> Archived : Deprecated / End of Life\n(Read-only for past students)
    
    Draft --> Archived : Cancelled Draft
    
    Archived --> [*]
```

#### State Machine 2: Quiz Attempt Lifecycle
- **Source File:** [`docs/diagrams/state-quiz-attempt.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/state-quiz-attempt.mmd)

```mermaid
stateDiagram-v2
    [*] --> Initialized : Learner Opens Quiz Checkpoint

    Initialized --> InProgress : Start Attempt\n(Attempt count < max_attempts;\nLock timer)

    state InProgress {
        [*] --> AnsweringQuestions
        AnsweringQuestions --> UpdatingSelections : Learner selects choices
        UpdatingSelections --> AnsweringQuestions : Next Question
    }

    InProgress --> Submitted : Explicit User Submission\n(Before deadline)
    
    InProgress --> AutoSubmitted : Time Limit Expiry\n(Backend timer threshold)

    Submitted --> Graded : Server Calculates Points\n(Atomically validates answers)
    
    AutoSubmitted --> Graded : Server Grades Partial Responses

    state Graded {
        [*] --> ScoreCalculated
        ScoreCalculated --> Passed : score >= passing_score_percent\n(Triggers Mastery Update)
        ScoreCalculated --> Failed : score < passing_score_percent\n(Triggers Remedial Branch)
    }

    Passed --> Completed : High Score Recorded
    
    Failed --> Completed : Max Attempts Reached
    
    Failed --> InProgress : Retake Attempt\n(Attempt count < max_attempts)

    Completed --> [*]
```

---

### 4.7 Production Deployment Topology
- **Source File:** [`docs/diagrams/deployment.mmd`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/diagrams/deployment.mmd)

```mermaid
flowchart TB
    subgraph ClientEnvironment [User Edge Devices]
        DesktopBrowser["Desktop Web Browser\n(Chrome / Safari / Firefox / Edge)"]
        MobileBrowser["Mobile Web Browser\n(iOS / Android Responsive Viewports)"]
    end

    subgraph EdgeTier [Global Edge & Content Delivery Network]
        CloudflareCDN["Edge CDN & TLS Termination\n(Global Caching, DDoS Protection)"]
    end

    subgraph FrontendCluster [Frontend Hosting Environment - Vercel / Node.js]
        NextServer["Next.js Application Server (App Router)\n(SSR Pages, Static Site Generation, Client Bundles)"]
    end

    subgraph BackendCluster [Backend Application Cluster - Docker Containers]
        NginxProxy["Nginx Reverse Proxy & Static Asset Server"]
        
        subgraph WebInstances [Stateless Django API Workers]
            Django1["Django Gunicorn Worker #1\n(/api/v1/*)"]
            Django2["Django Gunicorn Worker #2\n(/api/v1/*)"]
        end

        subgraph CeleryCluster [Asynchronous Task Worker Fleet]
            CeleryWorker1["Celery Worker (Media & Validation)"]
            CeleryWorker2["Celery Worker (Analytics & Adaptive)"]
            CeleryBeat["Celery Beat Periodic Scheduler"]
        end
    end

    subgraph CachingAndQueue [In-Memory State & Broker]
        RedisInstance[("Redis Cache & Task Broker\n(Port 6379)")]
    end

    subgraph StorageCloud [Cloud Infrastructure & Persistent Services]
        S3Bucket[("S3-Compatible Object Storage\n(Media Binaries, Transcripts, Thumbs)")]
        
        subgraph NeonCloud [Neon Serverless PostgreSQL Cloud]
            NeonPooler[("Neon PgBouncer Connection Pooler\n(Runtime Query Port 6543)")]
            NeonDirect[("Neon Direct PostgreSQL Node\n(Migration & Admin Port 5432)")]
        end
    end

    DesktopBrowser --> CloudflareCDN
    MobileBrowser --> CloudflareCDN

    CloudflareCDN -- "HTML / JS / CSS" --> NextServer
    CloudflareCDN -- "Media Asset Streaming" --> S3Bucket
    CloudflareCDN -- "API Traffic (/api/v1/*)" --> NginxProxy

    NextServer -- "Server-Side Fetch /api/v1/*" --> NginxProxy
    
    NginxProxy --> Django1
    NginxProxy --> Django2

    Django1 --> RedisInstance
    Django2 --> RedisInstance

    Django1 -- "App Queries (Pooled)" --> NeonPooler
    Django2 -- "App Queries (Pooled)" --> NeonPooler
    Django1 -- "Schema Migrations (Direct)" --> NeonDirect

    Django1 -- "Enqueue Async Tasks" --> RedisInstance
    Django2 -- "Enqueue Async Tasks" --> RedisInstance

    RedisInstance -- "Job Queues" --> CeleryWorker1
    RedisInstance -- "Job Queues" --> CeleryWorker2
    CeleryBeat -- "Schedules Periodic Tasks" --> RedisInstance

    CeleryWorker1 --> S3Bucket
    CeleryWorker1 --> NeonPooler
    CeleryWorker2 --> NeonPooler

    DesktopBrowser -. "Direct Presigned Upload" .-> S3Bucket
    MobileBrowser -. "Direct Presigned Upload" .-> S3Bucket
```

---

## 5. Abstract Models & Adaptive Innovation (Rubric C2)

### 5.1 Innovation Rationale: Knowledge-Space Adaptive Personalization
Traditional online learning management systems enforce rigid, monolithic curricula where all students must traverse identical linear content sequences regardless of prior competency or learning velocity. In contrast, the **FutureLearning Adaptive Engine** implements a mathematically rigorous **Knowledge-Space Theory (KST)** model ([`D-008`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-008-knowledge-space-skill-graph-and-pluggable-adaptive-engine)). 

The architecture models knowledge as an abstract **Directed Acyclic Graph (DAG)** of atomic competencies ($\mathcal{S}$), associating instructional content and assessment items with weighted skill vectors.

```text
       [Skill S1: Basic Syntax]
                  |
                  v
       [Skill S2: Data Structures]
         /                     \
        v                       v
[Skill S3: Recursion]    [Skill S4: Search Algorithms]
        \                       /
         v                     v
       [Skill S5: Dynamic Programming]
```

### 5.2 Mathematical Formalization of the Learner Model
1. **Skill Space:** Let $\mathcal{S} = \{s_1, s_2, \dots, s_N\}$ be the finite set of academic skills within a course domain.
2. **Prerequisite Partial Order:** Let $\prec$ denote the strict partial order of prerequisites over $\mathcal{S}$, where $s_i \prec s_j$ signifies that mastery of $s_i$ is a mandatory pedagogical prerequisite for studying $s_j$.
3. **Learner Mastery State Vector:** For any learner $u$, their mastery state is represented as a real-valued vector:
   $$\mathbf{M}_u = \big(m(u, s_1), m(u, s_2), \dots, m(u, s_N)\big) \quad \text{where } m(u, s_i) \in [0.0, 1.0]$$
4. **Assessment Skill Mapping:** Each assessment question $q$ is linked to a target skill $s(q)$ with an item discrimination weight $w_q \in (0.0, 1.0]$.
5. **Mastery Updating Algorithm:** When learner $u$ completes assessment attempt $a$, their skill mastery score is updated using an Exponentially Weighted Moving Average (EWMA):
   $$m_{t+1}(u, s) = (1 - \alpha) \cdot m_t(u, s) + \alpha \cdot \left(\frac{\sum_{q \in Q_s} \text{awarded\_points}(q)}{\sum_{q \in Q_s} \text{max\_points}(q)}\right)$$
   Where $\alpha = 0.35$ is the empirical learning sensitivity coefficient.

### 5.3 Pluggable Strategy Pattern Architecture
To decouple mathematical heuristic rules from business controllers, the engine is encapsulated behind a strict strategy interface:

```python
# backend/apps/learning/strategies/base.py
from abc import ABC, abstractmethod
from typing import List
from apps.users.models import User
from apps.courses.models import Course, Lesson

class RecommendationItem:
    def __init__(self, lesson: Lesson, reason: str, is_remedial: bool):
        self.lesson = lesson
        self.reason = reason
        self.is_remedial = is_remedial

class AdaptiveStrategy(ABC):
    @abstractmethod
    def evaluate_mastery(self, user: User, attempt_id: str) -> None:
        """Update learner skill mastery vector upon quiz attempt submission."""
        pass

    @abstractmethod
    def generate_recommendations(self, user: User, course: Course) -> List[RecommendationItem]:
        """Generate ordered list of next, remedial, or enrichment lessons."""
        pass
```

- **Default Implementation (`RuleBasedAdaptiveStrategy`):**
  - **Remedial Trigger ($m(u, s) < 0.70$):** Identifies the lowest-scoring unmastered skill $s_{fail}$, traverses the DAG backward to find unmastered prerequisite lessons, and injects them as high-priority remedial units with transparent justification (*"Recommended because your score on 'Recursion' was 58%"*).
  - **Enrichment Trigger ($m(u, s) \ge 0.85$):** Unlocks advanced elective lessons associated with child nodes in the skill graph, challenging high-performing learners.
- **Future ML Capability:** Enables data science teams to drop in reinforcement learning (e.g., Deep Q-Networks) or collaborative filtering models in Phase 11 without refactoring database models or client API contracts.

---

## 6. Content Model & Non-Technical Authoring

### 6.1 Composite ContentBlock Architecture
To satisfy the core requirement that non-technical content designers can build and update diverse media without programming (`FR-CRS-04`, `FR-CRS-05`, `NFR-USAB-01`), lessons are composed of ordered, polymorphic `ContentBlock` instances ([`D-009`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-009-composite-contentblock-architecture-and-draftpublish-versioning)):

```text
Course (Metadata, Slug, Category, Difficulty, Status)
  └── Module (Title, Description, Position)
        └── Lesson (Title, Duration, is_required, is_preview)
              ├── ContentBlock #1: Rich Text / Markdown
              ├── ContentBlock #2: Media Asset (Video with synchronized VTT captions)
              ├── ContentBlock #3: Interactive Simulation (Sandboxed iframe)
              └── ContentBlock #4: Formative Quiz (Assessment Checkpoint)
```

### 6.2 Safe Draft / Publish Versioning Workflow
Modifying a live course without breaking enrolled students' progress represents a severe risk in e-learning platforms. The platform implements a **Copy-on-Write Versioning Protocol**:
1. When an instructor edits a `PUBLISHED` course, the system creates a draft revision snapshot.
2. Active learners continue reading published versions from the cached CDN and Redis layers without disruption.
3. Once the instructor finishes editing and validates prerequisites, clicking **Publish**:
   - Updates `Course.status = PUBLISHED` and increments `version_number`.
   - Atomically updates lesson block relationships.
   - Dispatches a Redis cache invalidation event across `fl:crs:{id}:*` keys.

---

## 7. Caching & Performance Architecture (NFR-PERF-01)

### 7.1 Multi-Layer Redis Caching Strategy
To achieve the strict target of **$p95 < 300\text{ ms}$** read latency under 10,000 concurrent active users, Redis is deployed as a high-speed cache-aside layer ([`D-010`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-010-multi-layer-redis-caching-and-event-invalidation-protocol)):

| Cache Key Pattern | Cached Data Payload | TTL | Invalidation Event / Trigger |
|---|---|---|---|
| `fl:cat:list` | Serialized top-level category taxonomy | 24 Hours | Category creation / update in `apps.courses` |
| `fl:crs:public:catalog` | Paginated published course catalog with filters | 15 Minutes | Course publication, title edit, or category change |
| `fl:crs:{slug}:detail` | Full course metadata, module list, public syllabus | 1 Hour | Course/Module/Lesson CRUD or publish action |
| `fl:user:{id}:profile` | User identity, role, active enrollments list | 30 Minutes | Profile update, role assignment, or new enrollment |
| `fl:user:{id}:progress:{crs_id}` | Learner completed lesson IDs and overall progress % | 10 Minutes | Lesson completion event or progress reset |
| `fl:throttle:{ip}:{endpoint}` | Sliding-window request counter for rate limiting | 60 Seconds | Automated Redis TTL expiry |

---

## 8. Asynchronous Task Worker Fleet (Celery Catalogue)

All background workloads are catalogued and assigned to dedicated Redis message queues:

| Task Function Name | Target Queue | Trigger Event | Retry Policy | Timeout |
|---|---|---|---|---|
| `content.tasks.validate_media_asset` | `media` | Direct upload confirmation (`POST /media-assets/confirm/`) | 3 retries, exponential backoff (10s, 30s, 90s) | 300s |
| `content.tasks.generate_video_thumbnails` | `media` | Successful video validation | 2 retries | 600s |
| `learning.tasks.recompute_learner_mastery` | `adaptive` | Quiz attempt submission or simulation score report | 3 retries, 5s delay | 60s |
| `learning.tasks.generate_adaptive_path` | `adaptive` | Student mastery update or on-demand path regeneration | 2 retries | 120s |
| `notifications.tasks.dispatch_event_alert` | `notifications` | Forum reply, quiz grade release, announcement | 5 retries | 30s |
| `analytics.tasks.aggregate_hourly_rollups` | `analytics` | Celery Beat periodic schedule (`0 * * * *`) | No retry (runs next cycle) | 900s |
| `users.tasks.export_user_data_archive` | `default` | User GDPR export request (`POST /me/export/`) | 2 retries | 300s |

---

## 9. Security, Privacy & Compliance Architecture

```text
+-------------------------------------------------------------------------------------------------+
|                                 DEFENSE-IN-DEPTH SECURITY MODEL                                 |
+--------------------------+------------------------------+---------------------------------------+
|   AUTHENTICATION & RBAC  |      DATA PROTECTION         |         APPLICATION HARDENING         |
| SimpleJWT Access (15m)   | HTTPS / TLS 1.3 Strict       | Strict CSP & Frame Sandboxing         |
| Rotating Refresh (7d)    | Passwords: PBKDF2 SHA-256    | Redis Rate Limiting (100 req/min)     |
| 5-Tier Server Guard      | GDPR Export & Erasure Logic  | Zero Raw SQL; ORM Parameterization   |
+--------------------------+------------------------------+---------------------------------------+
```

1. **Authentication & Token Rotation (`FR-AUTH-03`):** Access tokens expire in 15 minutes. Refresh tokens rotate on every invocation; previously used refresh tokens are blacklisted immediately in Redis.
2. **Access Control Matrix (`FR-AUTH-02`, `D-006`):**
   - `Guest`: Read public catalog (`GET /courses/`), read preview lessons.
   - `Learner`: Write enrollments (`POST /courses/{id}/enroll/`), write progress, submit quizzes.
   - `Instructor`: Full CRUD on owned courses, modules, lessons, assessments, and analytics.
   - `Moderator`: Manage reported forum posts (`POST /discussions/{id}/moderate/`).
   - `Administrator`: Global user role assignment, category CRUD, system configuration.
3. **Question Key Protection (`FR-ASM-02`):** `Choice.is_correct` is excluded from DRF serializer contexts for learner requests, making client-side answer sniffing physically impossible.
4. **GDPR Data Portability & Erasure (`FR-AUTH-05`, `NFR-PRIV-01`):**
   - Data export generates an encrypted, machine-readable JSON archive containing user profile, enrollments, quiz attempts, and forum posts.
   - Account erasure anonymizes student records (`email = "deleted_user_{uuid}@deleted.futurelearning.org"`, `first_name = "Deleted"`, `last_name = "User"`), scrubbing PII while preserving historical course aggregate counts.

---

## 10. Scalability & High-Load Architecture (NFR-SCAL-01)

1. **Stateless Web API Layer:** All session state resides in signed JWTs or Redis. Django application containers can scale horizontally across $N$ replicas behind Nginx.
2. **Neon Connection Management:**
   - **Runtime Queries:** Application workers connect to Neon via **PgBouncer** connection pooling (`ep-ancient-wildflower-b3hehj34-pooler.c-4.ap-southeast-1.aws.neon.tech`), maintaining persistent connection pools with `conn_max_age=60` and `conn_health_checks=True`.
   - **Migrations & DDL:** Django management commands (`python manage.py migrate`) utilize the direct PostgreSQL connection (`port 5432`) to prevent pooler lockups.
3. **Direct S3 Binary Uploads:** Large media files never transit Django web worker memory, eliminating worker thread exhaustion during high concurrency.
4. **Database Query Indexing:**
   - Composite index on `Course (status, category_id)` for sub-50ms catalog filtering.
   - Unique composite index on `Enrollment (learner_id, course_id)` for single-enrollment guarantee.
   - Unique composite index on `LessonProgress (enrollment_id, lesson_id)` for idempotent progress upserts.
   - Composite index on `QuizAttempt (enrollment_id, assessment_id, attempt_number)` for fast attempt counting.

---

## 11. Requirements-to-Component Traceability Matrix

| Requirement ID | Module / Component | Primary Model / Class | API Endpoint / Service File |
|---|---|---|---|
| `FR-AUTH-01` | Auth & User | `apps.users.models.User` | `POST /api/v1/auth/register/` |
| `FR-AUTH-02` | Auth & User | `apps.users.permissions.IsRole` | `backend/apps/users/permissions.py` |
| `FR-AUTH-03` | Auth & User | `rest_framework_simplejwt` | `POST /api/v1/auth/login/`, `/token/refresh/` |
| `FR-AUTH-04` | Auth & User | `apps.users.services.PasswordReset` | `POST /api/v1/auth/password-reset/` |
| `FR-AUTH-05` | Auth & User | `apps.users.models.UserConsent` | `backend/apps/users/models.py` |
| `FR-CRS-01` | Course | `apps.courses.models.Course` | `GET /api/v1/courses/` |
| `FR-CRS-02` | Course | `apps.courses.models.Course` | `GET /api/v1/courses/{id}/` |
| `FR-CRS-03` | Enrollment | `apps.enrollments.models.Enrollment` | `POST /api/v1/courses/{id}/enroll/` |
| `FR-CRS-04` | Course / Content | `Module`, `Lesson` | `backend/apps/content/models.py` |
| `FR-CRS-05` | Content | `apps.content.models.ContentBlock` | `backend/apps/content/models.py` |
| `FR-CRS-06` | Course | `apps.courses.services.PublishService` | `POST /api/v1/courses/{id}/publish/` |
| `FR-CRS-07` | Course | `apps.courses.models.CourseVersion` | `backend/apps/courses/models.py` |
| `FR-MED-01` | Media | `apps.content.models.MediaAsset` | `POST /api/v1/lessons/{id}/media-upload-url/` |
| `FR-MED-02` | Media | `apps.content.tasks.validate_media` | `backend/apps/content/tasks.py` |
| `FR-MED-03` | Media / Player | `MediaAsset.captions_url` | `frontend/src/components/player/MediaPlayer.tsx` |
| `FR-PER-01` | Adaptive Learning | `Skill`, `LessonSkill` | `backend/apps/learning/models.py` |
| `FR-PER-02` | Adaptive Learning | `apps.learning.models.StudentSkill` | `backend/apps/learning/services/mastery.py` |
| `FR-PER-03` | Adaptive Learning | `apps.learning.strategies.RuleBased`| `backend/apps/learning/strategies/` |
| `FR-PER-04` | Adaptive Learning | `LearningPath`, `LearningPathItem` | `GET /api/v1/me/learning-path/` |
| `FR-PER-05` | Adaptive Learning | `AdaptiveStrategy` Interface | `backend/apps/learning/strategies/base.py` |
| `FR-TRK-01` | Progress | `apps.progress.models.LessonProgress`| `PATCH /api/v1/lessons/{id}/progress/` |
| `FR-TRK-02` | Progress / Enroll | `apps.progress.services.Completion` | `POST /api/v1/lessons/{id}/complete/` |
| `FR-TRK-03` | Progress / UI | `LearnerDashboardView` | `frontend/src/app/dashboard/page.tsx` |
| `FR-ASM-01` | Assessment | `Assessment`, `Question`, `Choice` | `POST /api/v1/lessons/{id}/assessment/` |
| `FR-ASM-02` | Assessment | `apps.assessments.services.Grader` | `POST /api/v1/attempts/{id}/submit/` |
| `FR-ASM-03` | Assessment | `QuizAttempt.attempt_number` | `backend/apps/assessments/models.py` |
| `FR-ASM-04` | Assessment | `apps.assessments.serializers` | `GET /api/v1/attempts/{id}/result/` |
| `FR-SIM-01` | Simulation | `SimulationBlock` | `frontend/src/components/player/SimulationFrame.tsx` |
| `FR-SIM-02` | Simulation | `postMessage` Handshake Contract | `frontend/src/lib/simulationProtocol.ts` |
| `FR-SIM-03` | Simulation / Prog | `apps.progress.services.SimScore` | `POST /api/v1/lessons/{id}/sim-score/` |
| `FR-DIS-01` | Discussion | `apps.discussions.models.Thread` | `GET/POST /api/v1/courses/{id}/discussions/` |
| `FR-DIS-02` | Discussion | `apps.discussions.models.Post` | `POST /api/v1/discussions/{id}/posts/` |
| `FR-DIS-04` | Discussion | `apps.discussions.models.Report` | `POST /api/v1/discussions/{id}/report/` |
| `FR-DIS-05` | Discussion / Mod | `apps.discussions.services.ModQueue` | `POST /api/v1/discussions/{id}/moderate/` |
| `FR-ANL-01` | Analytics | `apps.analytics.models.CourseRollup` | `GET /api/v1/courses/{id}/analytics/` |
| `FR-ADM-01` | Administration | `apps.users.views.AdminUserViewSet` | `GET/PATCH /api/v1/admin/users/` |
| `FR-ADM-02` | Administration | `apps.courses.models.Category` | `GET/POST /api/v1/categories/` |
| `NFR-PERF-01`| Performance / Cache| Redis Cache-Aside & Connection Pool| `backend/config/settings.py` |
| `NFR-SCAL-01`| Scalability / Infra| Docker Compose Stateless Replicas | `infra/docker-compose.yml` |
| `NFR-A11Y-01`| Accessibility | Next.js Accessible Design Primitives| `frontend/src/components/ui/*` |
| `NFR-USAB-01`| Authoring Usability| Content Designer Studio WYSIWYG | `frontend/src/app/studio/page.tsx` |
| `NFR-PRIV-01`| Privacy / GDPR | `users.tasks.export_user_data` | `POST /api/v1/me/export/` |
