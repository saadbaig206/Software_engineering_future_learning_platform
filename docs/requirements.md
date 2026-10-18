# Requirements Specification — FutureLearning Learning Engine

## 1. Purpose and source boundary
The supplied CCP brief describes a scalable, user-friendly, secure online learning platform for diverse subjects. It calls for flexible and personalized learning, adaptive learning paths, progress tracking, multiple media formats (text, video, audio, interactive elements), quizzes, simulations, discussion forums, accessibility, frequent content updates by non-technical staff, UML/system design, test cases, and a PERT/CPM project plan.

The requirements below translate that brief into a buildable proposal. Details not explicitly defined in the brief (for example, exact roles, score thresholds, performance targets, and retention periods) are labelled as proposed assumptions and should be confirmed with the instructor/team.

## 2. Goals
- G1: Deliver a responsive, accessible learning experience across modern desktop and mobile browsers.
- G2: Allow content designers to create and update courses without programming.
- G3: Support text, video, audio, documents, quizzes, and interactive learning activities.
- G4: Track lesson/course progress and resume where a learner stopped.
- G5: Adapt recommendations and learning paths based on learner performance.
- G6: Support discussions and useful analytics.
- G7: Protect learner data and enforce permissions on the server.
- G8: Keep the system modular and capable of scaling as usage grows.

## 3. Actors
- Learner (proposed role): discovers courses, enrolls, studies lessons, completes assessments, tracks progress, receives recommendations, and participates in discussions.
- Instructor/content designer (proposed role): creates, edits, orders, previews, and publishes course content; creates assessments; reviews course analytics.
- Administrator (proposed role): manages accounts, roles, categories, moderation, and platform configuration.

## 4. Functional requirements
Priority: P0 = MVP, P1 = important after MVP, P2 = future enhancement.

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---:|---|
| FR-01 | Account registration and login | P0 | A valid account can register and authenticate; invalid credentials are rejected without revealing sensitive details. |
| FR-02 | Role-based authorization | P0 | API endpoints enforce learner/instructor/admin permissions server-side. |
| FR-03 | Course discovery and details | P0 | Users can list, filter, and view published courses and their metadata. |
| FR-04 | Course authoring | P0 | Authorized instructors can create and edit draft courses and organize modules/lessons. |
| FR-05 | Content publishing workflow | P0 | Draft content is not visible as published content; authorized users can publish/unpublish. |
| FR-06 | Multi-format learning content | P0 | Lessons can represent text, video, audio, document, quiz, or interactive content; media metadata is stored separately from file bytes. |
| FR-07 | Enrollment | P0 | A learner can enroll in a published course; duplicate enrollments are prevented. |
| FR-08 | Lesson progress | P0 | The system records status, completion time, and optional media position for an enrolled learner. |
| FR-09 | Course progress calculation | P0 | Progress is calculated from required lessons and is consistent with lesson progress records. |
| FR-10 | Assessment authoring | P0 | Authorized instructors can create assessments, questions, choices, points, and ordering. |
| FR-11 | Assessment attempts and scoring | P0 | Learners can submit answers; score is calculated on the server and an attempt/result is stored. |
| FR-12 | Adaptive recommendations | P1 | The system recommends revision/practice/next lessons using explainable rules based on recent assessment results and mastery. |
| FR-13 | Learning paths | P1 | A learner can view an ordered path of recommended lessons with a reason for each recommendation. |
| FR-14 | Discussions | P1 | Enrolled learners can create discussion threads and replies; moderation permissions apply. |
| FR-15 | Learner dashboard | P0 | Learner sees active courses, progress, and continue-learning links. |
| FR-16 | Instructor analytics | P1 | Instructor sees enrollment, completion, assessment, and lesson drop-off summaries for courses they own. |
| FR-17 | Notifications | P2 | Users can see in-app notifications for defined events. |
| FR-18 | Admin management | P1 | Admin can manage users, categories, course moderation, and reported discussion content. |
| FR-19 | Accessibility support | P0 | Main flows are keyboard operable; form labels, focus states, semantic structure, captions/transcripts and alt text are supported where relevant. |
| FR-20 | Search/filter | P1 | Course catalogue supports search and useful filters such as category and difficulty. |

## 5. Non-functional requirements
Targets below are proposed engineering targets, not statements from the source brief.

| ID | Requirement | Proposed target / validation |
|---|---|---|
| NFR-01 Performance | Common API reads should usually complete within 500 ms at agreed test load, excluding media transfer and cold starts. Measure with repeatable tests. |
| NFR-02 Scalability | Stateless Django web processes can be replicated; media is served from object storage/CDN rather than through application workers for every byte. |
| NFR-03 Security | HTTPS in production; secret values in environment/secret manager; server-side authorization; validated uploads; secure cookie/token strategy; dependency updates. |
| NFR-04 Privacy | Collect only necessary learner data; document purpose, access, retention, deletion, and export expectations before launch. |
| NFR-05 Accessibility | Target WCAG 2.2 AA as an engineering goal; audit key flows with keyboard and automated/manual checks. |
| NFR-06 Compatibility | Support current stable versions of major desktop/mobile browsers agreed by the team. |
| NFR-07 Maintainability | Separate Django apps by domain; business logic in service modules; tests for critical rules; version API under `/api/v1/`. |
| NFR-08 Reliability | Database constraints protect key invariants; backups/restore options are understood and tested. |
| NFR-09 Usability | A content designer can create a draft course, add a module/lesson, preview it, and publish it without writing code. Validate with a usability walkthrough. |
| NFR-10 Observability | Production errors, request latency, task failures, and database health can be inspected without logging passwords/tokens or unnecessary personal data. |

## 6. Business rules
- BR-01: Only published courses appear in the public catalogue.
- BR-02: Only an authorized instructor/administrator may create or modify course content.
- BR-03: A learner has at most one enrollment per course unless a future re-enrollment policy explicitly allows otherwise.
- BR-04: Learner progress is scoped to the learner and lesson; only the owner or authorized staff may read/update it.
- BR-05: Correct answers and scoring logic are never trusted from the browser; the server computes results.
- BR-06: Course completion is based on required lessons, with the exact policy documented and tested.
- BR-07: Recommendations explain their reason (e.g. “revision suggested because recent score was below the configured threshold”).
- BR-08: Media files live in object storage; PostgreSQL stores metadata and references, not large media binaries.
- BR-09: A course/lesson cannot be accessed merely by guessing its ID; permissions and enrollment/publication status are checked by the API.

## 7. Assumptions and open decisions
1. Roles are learner, instructor/content designer, and administrator.
2. The first release uses a single Django application split into modular apps, not microservices.
3. Course access is free for MVP; payment/subscription is out of scope unless required by the instructor.
4. Initial adaptive recommendations are rule-based and explainable, not ML-based.
5. Video hosting/transcoding is not built from scratch; use object storage or a media provider.
6. Simulation content is represented as an interactive lesson type; its exact runtime format is to be decided.
7. The instructor/team must confirm whether certificates, email notifications, SCORM/xAPI, multilingual UI, grading review, and re-enrollment are required.
8. Performance/load targets must be revised when expected concurrent users and hosting are known.

## 8. MVP scope
Include: auth/roles, course catalogue, authoring, modules/lessons, media metadata, enrollment, progress, quiz attempts/scoring, simple rule-based recommendations, student dashboard, basic instructor course metrics, and core accessibility.

Defer: payments, AI chatbot, ML recommender, live streaming, mobile app, microservices, Kubernetes, complex real-time collaboration, and sophisticated simulation authoring.
