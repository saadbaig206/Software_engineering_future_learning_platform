# Requirements Specification — FutureLearning Learning Engine

**Document Reference:** `docs/01-requirements.md`  
**Phase:** Phase 1 — Requirements Specification  
**Course Context:** Complex Computing Problem (CCP) — Software Engineering (CLO-2, CLO-3)  
**Rubric Mapping:** C1 Clarity of Objective, C2 Innovation, C3 Modularity, C4 Validation, C5 Planning  
**Status:** Approved Baseline  

---

## 1. Purpose & Source Context

FutureLearning Corporation is an established distance-learning enterprise operating in an increasingly competitive global education market. To maintain educational leadership and scale operations, FutureLearning requires the **FutureLearning Learning Engine**: a modular, personalized, accessible, and secure digital learning platform delivering flexible instruction across diverse academic and professional subjects.

This document compiles the formal **Requirements Specification** for the platform. It translates the university Complex Computing Problem (CCP) brief into unambiguous, measurable, and testable engineering specifications. Every functional and non-functional requirement is assigned a unique identifier, a MoSCoW priority, rigorous acceptance criteria, and a concrete justification linking the capability to FutureLearning's strategic business, pedagogical, and accessibility objectives.

---

## 2. Strategic Platform Goals

- **G-01 (Flexible Multi-Format Pedagogy):** Deliver rich multi-format instruction—combining structured text, high-definition streaming video, audio lectures, downloadable documents, interactive simulations, and formative/summative quizzes.
- **G-02 (Empowered Non-Technical Authoring):** Enable subject matter experts and content designers to author, organize, preview, and update rich coursework through an intuitive studio without requiring programming knowledge or manual database interventions.
- **G-03 (Granular Progress & Resume Telemetry):** Maintain uninterrupted learner journeys by persisting granular progress events, completion states, and media playback positions across devices.
- **G-04 (Adaptive Personalized Learning):** Dynamically calibrate student learning pathways based on assessed skill mastery, providing explainable automated remediation for struggling learners and enrichment challenges for high achievers.
- **G-05 (Collaborative Learning Communities):** Foster student-to-student and student-to-instructor engagement through contextual discussion forums, moderated communication channels, and real-time alerts.
- **G-06 (Actionable Educational Insights):** Provide instructors and platform administrators with actionable telemetry regarding course engagement, drop-off bottlenecks, and assessment item discrimination.
- **G-07 (Universal Accessibility & Inclusivity):** Guarantee universal access for all learners, including individuals with visual, motor, auditory, or cognitive disabilities, adhering strictly to **WCAG 2.1 Level AA** standards.
- **G-08 (Cloud-Scale Elasticity & Trust):** Protect learner data privacy under GDPR principles, resist OWASP top security vulnerabilities, and handle global traffic spikes through stateless horizontal elasticity.

---

## 3. Stakeholders & User Roles

The platform enforces a five-tier Role-Based Access Control (RBAC) model ([`D-006`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-006-five-tier-role-taxonomy-and-rbac-model)), separating operational, pedagogical, and governance responsibilities:

```text
       +-------------------------------------------------------+
       |                  Platform Administrator               |
       |  (User & Role Governance, Platform Config, Telemetry) |
       +---------------------------+---------------------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
+-------------------------------+             +-------------------------------+
|    Instructor / Designer      |             |           Moderator           |
| (Course Authoring, Analytics) |             |  (Community Forum Moderation) |
+---------------+---------------+             +---------------+---------------+
                |                                             |
                +----------------------+----------------------+
                                       |
                                       v
                        +-------------------------------+
                        |            Learner            |
                        | (Enrolled Student Experience) |
                        +---------------+---------------+
                                       |
                                       v
                        +-------------------------------+
                        |             Guest             |
                        | (Public Discovery & Syllabus) |
                        +-------------------------------+
```

1. **Guest (Unauthenticated Visitor):** Discovers published courses, inspects syllabus outlines, samples public preview lessons, and initiates account registration.
2. **Learner (Enrolled Student):** Enrolls in courses, interacts with multi-format learning blocks, attempts assessments, tracks skill mastery, receives personalized study paths, and participates in discussions.
3. **Instructor / Content Designer:** Non-technical subject matter expert who authors courses, modules, lessons, and quizzes; configures media metadata; previews drafts; and reviews student learning analytics.
4. **Moderator:** Community manager tasked with reviewing reported discussion content, locking toxic threads, hiding abusive posts, and maintaining academic integrity.
5. **Platform Administrator:** System supervisor managing user lifecycle, assigning roles, creating global course categories, auditing security logs, and configuring platform-wide parameters.

---

## 4. Stakeholder-to-Requirement Traceability Matrix

| Stakeholder / Role | Key Functional Modules Covered | Primary Non-Functional Concerns |
|---|---|---|
| **Guest** | `FR-AUTH-01`, `FR-AUTH-03`, `FR-CRS-01`, `FR-CRS-02` | `NFR-PERF-01`, `NFR-A11Y-01`, `NFR-COMP-01` |
| **Learner** | `FR-AUTH-01`–`05`, `FR-CRS-03`, `FR-MED-03`–`05`, `FR-PER-01`–`05`, `FR-TRK-01`–`04`, `FR-ASM-02`–`05`, `FR-SIM-01`–`03`, `FR-DIS-01`–`04`, `FR-NOT-01`–`03` | `NFR-PERF-01`, `NFR-A11Y-01`, `NFR-PRIV-01`, `NFR-COMP-01` |
| **Instructor / Designer** | `FR-CRS-04`–`07`, `FR-MED-01`–`02`, `FR-ASM-01`, `FR-ASM-06`, `FR-ANL-01`–`03` | `NFR-USAB-01`, `NFR-MAINT-01`, `NFR-SEC-01` |
| **Moderator** | `FR-DIS-04`, `FR-DIS-05`, `FR-NOT-01` | `NFR-SEC-01`, `NFR-USAB-01`, `NFR-PERF-01` |
| **Administrator** | `FR-ADM-01`–`04`, `FR-ANL-04`, `FR-AUTH-04`–`05` | `NFR-SEC-01`, `NFR-SEC-02`, `NFR-PRIV-01`, `NFR-AVAIL-01`, `NFR-SCAL-01` |

---

## 5. Functional Requirements (Grouped by Module)

### Module 1: Authentication & User Management (AUTH)

#### `FR-AUTH-01`: Learner Registration & Email Verification
- **Description:** Prospective learners can register with unique email address, password, first name, last name, and role. System dispatches a cryptographically signed verification email.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Rejects passwords with < 8 characters or failing standard complexity checks (CommonPasswordValidator).
  2. Prevents duplicate email registration with a generic, timing-attack-resistant message.
  3. User account remains unverified until one-time verification token is submitted; unverified accounts cannot access paid/restricted courses.
- **Justification:** Essential to ensure valid student identities, prevent spam registrations, and maintain contact channels for course updates.

#### `FR-AUTH-02`: Role-Based Access Control (RBAC) Enforcement
- **Description:** Server-side API middleware validates JWT claims on every incoming protected request, enforcing permissions matching the five-tier role taxonomy.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Endpoint access is strictly verified on the backend; frontend route guards are treated as convenience only.
  2. Any attempt by a `Learner` to access instructor or administrative endpoints yields an HTTP 403 Forbidden.
  3. Instructors can modify only courses they own, unless granted co-instructor permissions.
- **Justification:** Guarantees platform security and prevents horizontal and vertical privilege escalation.

#### `FR-AUTH-03`: JWT Lifecycle & Refresh Rotation
- **Description:** The system provides stateless JWT access tokens (15-minute lifetime) and rotating refresh tokens (7-day lifetime) persisted securely.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Access token issuance returns claims containing user UUID, email, and role.
  2. Refreshing an access token invalidates the consumed refresh token and issues a new pair (refresh token rotation).
  3. Blacklisted refresh tokens immediately prevent further token generation upon logout.
- **Justification:** Supports stateless horizontal scaling across web instances while mitigating token theft risks.

#### `FR-AUTH-04`: Password Reset & Account Recovery
- **Description:** Users can initiate self-service password recovery via a short-lived (15 minutes), single-use reset token sent to their registered email.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Password reset invalidates all active refresh tokens for the user account upon completion.
  2. Endpoint does not reveal whether an email address exists in the database.
- **Justification:** Minimizes administrative support overhead while preserving account security.

#### `FR-AUTH-05`: GDPR Consent Capture
- **Description:** The registration flow captures explicit, unbundled consent for terms of service, privacy policy, and optional learning analytics data processing.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Consent status, version timestamp, and IP address hash are immutably logged.
  2. Users can inspect and revoke optional data processing consents at any time in their profile settings.
- **Justification:** Mandatory compliance requirement for operating a global educational platform under GDPR and privacy regulations.

---

### Module 2: Course & Content Management (CRS)

#### `FR-CRS-01`: Public Course Catalog & Filter Engine
- **Description:** Unauthenticated and authenticated users can browse, search, and filter published courses by keyword, category, difficulty, and estimated duration.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Catalog search matches title, short description, and category slug with sub-second response times.
  2. Draft, under-review, and archived courses are strictly excluded from public catalog queries.
- **Justification:** Critical top-of-funnel discovery engine to drive student enrollment and engagement.

#### `FR-CRS-02`: Course Syllabus & Preview Inspection
- **Description:** Visitors can view the hierarchical outline (modules, lessons) of any published course, including lesson duration, required status, and designated free preview lessons.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Lessons marked `is_preview=True` can be streamed/read without course enrollment.
  2. Non-preview lesson content blocks remain restricted until enrollment is confirmed.
- **Justification:** Allows students to evaluate course curriculum quality before committing to enrollment.

#### `FR-CRS-03`: Course Enrollment Management
- **Description:** Authenticated learners can enroll in published courses with a single action, creating an immutable enrollment record.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Enrollment is idempotent; duplicate enrollments for the same user and course are prevented by unique DB constraint.
  2. System initializes a blank progress ledger for all required modules upon enrollment.
- **Justification:** Fundamental prerequisite for student tracking, assessment submission, and personalization.

#### `FR-CRS-04`: Hierarchical Course Authoring
- **Description:** Content designers can create and manage a four-level pedagogical hierarchy: `Course` > `Module` > `Lesson` > `ContentBlock`.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Content designers can reorder modules and lessons via drag-and-drop or sequential position numbers.
  2. Deleting a module triggers an explicit dependency check to prevent accidental loss of student progress data.
- **Justification:** Enables flexible structuring of complex academic courses into digestible instructional units.

#### `FR-CRS-05`: Multi-Type Content Block Authoring
- **Description:** Lessons can assemble multiple heterogenous content blocks: rich text (Markdown/HTML), streaming video, audio track, document (PDF), quiz checkpoint, and interactive simulation.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Text blocks support headings, code blocks, lists, blockquotes, and embedded figures.
  2. Every block maintains its own display position within the parent lesson.
- **Justification:** Satisfies core CCP objective to support diverse learning styles and multi-format media delivery.

#### `FR-CRS-06`: Draft, Review, and Publish Lifecycle
- **Description:** Courses transition through formal states: `DRAFT` → `IN_REVIEW` → `PUBLISHED` → `ARCHIVED`.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Publishing is blocked if a course has zero modules or if any module contains zero published lessons.
  2. Instructors can preview unpublished draft courses exactly as an enrolled learner would see them.
- **Justification:** Prevents incomplete, unverified, or broken course materials from being published to students.

#### `FR-CRS-07`: Course Content Versioning & Audit History
- **Description:** Content updates to published courses create an immutable version snapshot, allowing instructors to inspect revision history and restore prior states.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Modifying a published course creates a draft working copy without breaking active learners' ongoing sessions.
  2. Version restore reverts lesson block content to the chosen historical revision.
- **Justification:** Ensures safe iterative updates by non-technical content designers without risking data loss.

---

### Module 3: Media Delivery & Ingestion Pipeline (MED)

#### `FR-MED-01`: Presigned Direct-to-Storage Media Uploads
- **Description:** The system issues short-lived, presigned upload URLs allowing the content designer's browser to upload large media files directly to S3-compatible object storage.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Django validates user permissions, target lesson ID, MIME type, and file size (< 1 GB) before issuing signed ticket.
  2. Zero raw media binary bytes flow through Django application worker processes ([`D-003`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-003-provider-agnostic-storage-abstraction-with-presigned-uploads)).
- **Justification:** Eliminates memory starvation and connection pool exhaustion on web servers during large video uploads.

#### `FR-MED-02`: Asynchronous Media Validation & Processing
- **Description:** Upon upload confirmation, a Celery task verifies file magic bytes, checks for malware, generates image thumbnails, and extracts duration metadata.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Uploaded files failing magic-byte validation are immediately deleted from storage and marked `REJECTED`.
  2. Video and audio files automatically extract exact duration in seconds and update `MediaAsset.duration_seconds`.
- **Justification:** Protects the platform from malicious payloads and provides accurate time estimates for course completion.

#### `FR-MED-03`: Accessible Captions & Transcripts Storage
- **Description:** Media assets store associated VTT/SRT closed-caption tracks and full-text transcript URLs for all video and audio lessons.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Video player displays synchronized closed captions in the learner's selected language.
  2. An interactive transcript box allows learners to read and search lecture text.
- **Justification:** Mandatory requirement for WCAG 2.1 AA accessibility compliance and supporting hearing-impaired learners.

#### `FR-MED-04`: Low-Bandwidth Adaptive Streaming & Fallbacks
- **Description:** Video and audio assets support adaptive bitrate streaming and low-bandwidth fallback modes for learners on slow mobile connections.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Video player provides manual quality selector (360p, 720p, 1080p, and Audio-Only).
  2. Audio-only mode reduces data consumption by > 80% compared to standard video streaming.
- **Justification:** Fulfills FutureLearning's mission to deliver reliable distance education in low-bandwidth global regions.

#### `FR-MED-05`: Downloadable Learning Material Delivery
- **Description:** Instructors can attach downloadable supplementary files (PDF guides, code repositories, slide decks) with secure time-limited download links.
- **Priority:** Could Have (P2)
- **Acceptance Criteria:**
  1. Download links expire after 60 minutes and require active course enrollment.
- **Justification:** Enhances pedagogical depth for offline study and practical exercises.

---

### Module 4: Learning Paths & Adaptive Personalization (PER)

#### `FR-PER-01`: Pedagogical Skill Graph Modeling
- **Description:** The system models a directed knowledge graph of academic `Skills`, associating lessons with skills via contribution weights and defining prerequisite skill dependencies.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Each quiz question and lesson can map to one or more skills with a normalized weight (0.0 to 1.0).
  2. Skill prerequisite relationships prevent circular dependencies via validation at save time.
- **Justification:** Provides the formal mathematical foundation for adaptive pathways and competency-based education.

#### `FR-PER-02`: Student Mastery Score Computation
- **Description:** The platform tracks and updates a continuous mastery score (0–100%) for each learner across all encountered skills based on assessment outcomes.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Completing an assessment triggers a transaction updating `StudentSkill.mastery_score`.
  2. Scores are updated monotonically based on weighted performance on mapped questions.
- **Justification:** Essential for quantifying student capability and driving personalized interventions.

#### `FR-PER-03`: Explainable Remedial & Advanced Adaptive Branching
- **Description:** An explainable rule-based engine generates personalized recommendations: learners scoring < 70% receive targeted remedial reviews; learners scoring ≥ 85% unlock advanced enrichment challenges ([`D-004`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-004-user-scope-clarifications-and-operational-parameters)).
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Every generated recommendation includes a transparent human-readable reason (e.g., *"Recommended because your score on 'Dynamic Programming' was 62%"*).
  2. Remedial branches identify the specific prerequisite lessons needed to bridge the knowledge gap.
- **Justification:** Directly satisfies core CCP requirement for adaptive learning paths while avoiding black-box algorithmic confusion.

#### `FR-PER-04`: Dynamic Learning Path Assembly
- **Description:** Learners can view an ordered sequence of upcoming lessons dynamically adjusted to their progress, performance, and preferred pace.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. As learners complete recommended remedial units and demonstrate mastery, the active learning path updates.
  2. Learners can regenerate their path on-demand (rate-limited to 1 request per minute).
- **Justification:** Guides students through optimal learning sequences tailored to individual comprehension rates.

#### `FR-PER-05`: Pluggable Recommendation Strategy Interface
- **Description:** The adaptive recommendation service encapsulates its logic behind a clean strategy interface (`AdaptiveStrategy`), allowing future machine learning models to replace rule-based heuristics without altering client contracts.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Strategy interface defines standard methods: `get_recommendations(learner, course)` and `recompute_mastery(learner, assessment_result)`.
  2. Rule-based implementation is the default, fully tested via mock learner profiles.
- **Justification:** Demonstrates engineering innovation (Rubric C2) and architectural maintainability.

---

### Module 5: Progress Tracking & Resume Engine (TRK)

#### `FR-TRK-01`: Granular Lesson Progress Heartbeats
- **Description:** The learning client transmits periodic heartbeat events during video/audio playback and lesson reading, recording last position in seconds and completion percentage.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Heartbeat updates are debounced on the client (every 10 seconds) and processed idempotently by the backend.
  2. Progress state includes `status` (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`), `last_position_seconds`, and `completion_percent`.
- **Justification:** Guarantees learners can seamlessly resume exactly where they left off across different browser sessions.

#### `FR-TRK-02`: Deterministic Course Completion Evaluation
- **Description:** The system computes overall course progress percentage based on completed required lessons and marks an enrollment completed when all required units are finished.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Optional preview lessons do not artificially inflate or deflate completion percentage.
  2. Marking the final required lesson complete atomically transitions `Enrollment.status` to `COMPLETED` and records `completed_at`.
- **Justification:** Provides definitive academic completion records required for credentialing and certification.

#### `FR-TRK-03`: Student Progress Dashboard
- **Description:** A dedicated learner dashboard presents all active enrollments, overall completion bars, recent activity timestamps, and direct "Resume Learning" action buttons.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Dashboard loads in < 300 ms utilizing cached enrollment queries.
  2. Clicking "Resume" navigates directly to the most recent in-progress lesson and seeks media to `last_position_seconds`.
- **Justification:** Enhances learner retention and eliminates friction in returning to active study.

#### `FR-TRK-04`: Course Progress Reset & Re-study
- **Description:** Learners who have completed a course can reset their progress to study the material again while preserving historical quiz attempts in an archive.
- **Priority:** Could Have (P2)
- **Acceptance Criteria:**
  1. Progress reset prompts for explicit user confirmation.
  2. Historical quiz attempts remain accessible in academic audit logs.
- **Justification:** Supports lifelong learning and continuous review for certification exams.

---

### Module 6: Assessments & Auto-Grading (ASM)

#### `FR-ASM-01`: Multi-Format Assessment Authoring
- **Description:** Instructors can attach quizzes to lessons, configuring title, passing score percentage (default 70%), time limit in seconds, and instructor-configured maximum attempts (`max_attempts`) ([`D-004`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-004-user-scope-clarifications-and-operational-parameters)).
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Supports Question Types: Single Choice, Multiple Select, True/False, and Short Answer.
  2. Each question specifies points awarded and an optional post-submission explanation.
- **Justification:** Core pedagogical vehicle for validating student knowledge acquisition and feeding the adaptive engine.

#### `FR-ASM-02`: Server-Side Secure Quiz Scoring
- **Description:** Learners submit answers to the backend API, which grades the submission on the server, calculates awarded points, and determines pass/fail status.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Correct answer choices (`is_correct`) are **never** transmitted to the browser prior to submission.
  2. Partial credit is computed accurately for Multiple Select questions based on selected correct choices minus incorrect selections.
- **Justification:** Guarantees assessment integrity by preventing browser-based tampering or inspection of answer keys.

#### `FR-ASM-03`: Attempt Limits & Cool-down Enforcement
- **Description:** The server strictly enforces the instructor's configured `max_attempts` and optional cool-down periods between attempts.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Submitting an attempt after reaching `max_attempts` returns HTTP 400 Bad Request with code `max_attempts_exceeded`.
  2. The learner's highest recorded score is preserved as the definitive grade for course completion.
- **Justification:** Enforces academic discipline and prevents brute-force guessing on high-stakes assessments.

#### `FR-ASM-04`: Immediate Pedagogical Feedback
- **Description:** Upon attempt completion, learners receive detailed feedback displaying their score percentage, pass/fail status, and per-question explanations.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. If allowed by assessment settings, question explanations reveal why choices were correct or incorrect.
  2. Learner can review past attempt history with timestamps and score breakdowns.
- **Justification:** Promotes formative learning and error correction immediately following test submission.

#### `FR-ASM-05`: Timed Assessment Auto-Submission
- **Description:** For quizzes with a configured time limit, the server validates submission timestamps against start time and auto-grades responses when time expires.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Client displays an accessible countdown timer with visual and auditory warnings at 5 minutes and 1 minute remaining.
  2. Attempts submitted > 30 seconds after deadline expiry (allowing for network latency) are auto-submitted with answers recorded up to expiry.
- **Justification:** Prevents cheating and ensures fair testing conditions for all enrolled students.

#### `FR-ASM-06`: Question Bank Randomization & Shuffling
- **Description:** Assessments can pull a randomized subset of $N$ questions from a larger pool and shuffle answer choices per learner attempt.
- **Priority:** Could Have (P2)
- **Acceptance Criteria:**
  1. Question order and choice positions are randomized independently for each attempt.
- **Justification:** Deterrence against collusion and answer sharing among students.

---

### Module 7: Simulations & Interactive Content (SIM)

#### `FR-SIM-01`: Sandboxed Interactive Simulation Embeds
- **Description:** Lessons can embed interactive simulations (scientific models, coding sandboxes, virtual labs) inside a strictly sandboxed `<iframe>` element ([`D-004`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-004-user-scope-clarifications-and-operational-parameters)).
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. The `iframe` applies restrictive sandbox attributes: `sandbox="allow-scripts allow-same-origin"`.
  2. Direct DOM access between the parent LMS frame and child simulation frame is prohibited by cross-origin security boundaries.
- **Justification:** Safely isolates third-party or untrusted simulation code while supporting engaging practical learning.

#### `FR-SIM-02`: Bi-Directional Window `postMessage` Contract
- **Description:** A standardized JSON postMessage protocol governs communication between the learning platform player and the embedded simulation.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Protocol specification:
     - Initialization: `{ "type": "SIM_INIT", "payload": { "userId": "...", "lessonId": "..." } }`
     - Score Report: `{ "type": "SIM_SCORE_REPORT", "payload": { "scorePercent": 85, "completed": true } }`
  2. Parent frame validates `event.origin` before accepting message payloads.
- **Justification:** Enables plug-and-play integration of diverse external interactive lab tools through an open standard.

#### `FR-SIM-03`: Interactive Simulation Score Ingestion
- **Description:** Scores reported from verified simulation frames are validated by the backend and recorded as lesson progress and skill mastery events.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Score reports update `LessonProgress.completion_percent` and trigger skill mastery updates identical to quiz submissions.
- **Justification:** Connects hands-on practical simulation performance directly into the student's adaptive learning path.

---

### Module 8: Discussion Forums & Community (DIS)

#### `FR-DIS-01`: Course & Lesson Contextual Discussion Threads
- **Description:** Enrolled learners and instructors can initiate discussion threads linked either to the overall course or to specific lessons.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Threads display author name, role badge (`Instructor`, `Learner`), creation timestamp, and reply count.
  2. Only enrolled learners, instructors, and administrators can post new threads.
- **Justification:** Creates active peer learning communities and provides direct channels for clarifying difficult course concepts.

#### `FR-DIS-02`: Nested Discussion Replies
- **Description:** Community members can post replies to existing threads with support for single-level nesting (replying to a reply).
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Replies render chronologically with clear indentation indicating parentage.
  2. Original thread author and mentioned users receive in-app notifications.
- **Justification:** Facilitates coherent, structured academic discourse around complex subject topics.

#### `FR-DIS-03`: Instructor Answer Endorsement
- **Description:** Course instructors can mark a helpful reply as the "Accepted / Verified Answer" to pin it to the top of the thread.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Pinned answers display a distinct visual checkmark and "Verified Instructor Answer" badge.
- **Justification:** Directs struggling students immediately to vetted, authoritative solutions.

#### `FR-DIS-04`: Content Flagging & Reporting
- **Description:** Any authenticated user can report abusive, offensive, or inappropriate discussion posts with an explanatory reason category.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Flagged posts automatically enter the moderation queue.
  2. Reporting users receive confirmation that their report has been logged.
- **Justification:** Protects the platform from harassment, hate speech, and spam, maintaining a safe learning environment.

#### `FR-DIS-05`: Moderator Queue & Actions
- **Description:** Designated `Moderator` and `Administrator` users have access to a dedicated moderation dashboard to review reported content and take action.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Moderators can execute actions: `DISMISS_REPORT`, `HIDE_POST`, `LOCK_THREAD`, or `DELETE_POST`.
  2. Hiding a post replaces content with *"This post was removed by a moderator"* while preserving thread integrity.
- **Justification:** Fulfills regulatory compliance and community safety governance requirements.

---

### Module 9: Notifications Engine (NOT)

#### `FR-NOT-01`: Asynchronous In-App Event Dispatcher
- **Description:** The system dispatches real-time and in-app notifications for key lifecycle events: enrollment confirmation, discussion reply, quiz grade release, and new course announcements.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Notification creation is processed asynchronously via Celery workers to avoid adding latency to web requests.
  2. Notifications table records `recipient_id`, `type`, `title`, `message`, `read_at`, and `created_at`.
- **Justification:** Boosts student re-engagement and keeps learners informed of vital course developments.

#### `FR-NOT-02`: Notification Center & Read State
- **Description:** Learner topbar includes a notification bell icon with an unread badge counter and an interactive drawer to view and mark alerts as read.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Marking individual or all notifications as read updates database state and decrements badge count.
- **Justification:** Standard, intuitive SaaS UX pattern for managing incoming alerts.

#### `FR-NOT-03`: Email Notification Digest
- **Description:** Learners can opt in to receive daily or weekly email digests summarizing unread discussion replies and recommended lessons.
- **Priority:** Could Have (P2)
- **Acceptance Criteria:**
  1. Digest emails include a one-click unsubscribe link fulfilling CAN-SPAM regulations.
- **Justification:** Re-engages dormant learners who may not log into the web platform daily.

---

### Module 10: Analytics & Telemetry Reporting (ANL)

#### `FR-ANL-01`: Instructor Course Engagement Analytics
- **Description:** Course instructors can inspect aggregated analytics for their courses: total active enrollments, overall completion rate, and average time-to-complete.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Analytics dashboards load within < 500 ms by reading pre-aggregated rollup tables calculated via Celery Beat.
  2. Metrics update on a scheduled hourly background schedule.
- **Justification:** Empowers instructors to evaluate the overall pedagogical effectiveness of their courses.

#### `FR-ANL-02`: Lesson Drop-off & Funnel Bottleneck Identification
- **Description:** The analytics dashboard visualizes student drop-off across sequential lessons, highlighting lessons where high percentages of students stall.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Drop-off chart identifies lessons with > 25% stall rate for immediate instructor review.
- **Justification:** Provides actionable data to locate confusing curriculum sections and improve course retention.

#### `FR-ANL-03`: Assessment Item Difficulty & Discrimination Analysis
- **Description:** Instructors can view question-level performance summaries: percentage of students answering correctly and average time spent per question.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Identifies questions with unusually low success rates (< 20%) to detect potentially flawed or ambiguous prompts.
- **Justification:** Continuous quality improvement for assessment validity and fairness.

#### `FR-ANL-04`: Administrator Platform Telemetry
- **Description:** Administrators can review platform-wide operational health: total registered users, active daily learners, storage volume consumed, and API error rates.
- **Priority:** Should Have (P1)
- **Acceptance Criteria:**
  1. Administrative overview displays 7-day and 30-day growth trends across users and course enrollments.
- **Justification:** Supports capacity planning and infrastructure budget forecasting for platform operators.

---

### Module 11: Administration & Governance (ADM)

#### `FR-ADM-01`: User Management & Role Administration
- **Description:** Administrators can search all registered users, update account status (`is_active`), modify assigned roles (`Learner`, `Instructor`, `Moderator`), and initiate forced password resets.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Role promotions/demotions are logged with admin user ID and timestamp in an immutable audit ledger.
  2. Administrators cannot revoke their own superuser status to prevent accidental lockout.
- **Justification:** Fundamental governance capability for managing university faculty, staff, and student accounts.

#### `FR-ADM-02`: Global Category & Subject Taxonomy Management
- **Description:** Administrators can create, edit, reorder, and archive top-level subject categories (e.g., Computer Science, Business, Engineering) and associated URL slugs.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Archiving a category prevents new courses from using it while preserving existing assigned courses.
- **Justification:** Maintains structured catalog organization across expanding academic disciplines.

#### `FR-ADM-03`: Global Content Moderation & Course Takedown
- **Description:** Administrators can unpublish or archive any course violating institutional policies or quality standards.
- **Priority:** Must Have (P0)
- **Acceptance Criteria:**
  1. Unpublishing immediately removes the course from the public catalog and invalidates relevant Redis catalog cache entries.
- **Justification:** Ensures legal and institutional compliance against copyright infringement or policy breaches.

#### `FR-ADM-04`: System Configuration & Maintenance Mode
- **Description:** Administrators can configure platform-wide settings (e.g., maximum upload limits, default quiz attempt defaults, maintenance mode banner).
- **Priority:** Could Have (P2)
- **Acceptance Criteria:**
  1. Toggling maintenance mode displays a friendly message to regular users while allowing administrators to log in.
- **Justification:** Enables controlled platform upgrades and zero-data-loss maintenance windows.

---

## 6. Non-Functional Requirements (Quantitative & Architectural)

```text
+-----------------------------------------------------------------------------------------+
|                               NON-FUNCTIONAL PILLARS                                    |
+--------------------------+------------------------------+-------------------------------+
|       PERFORMANCE        |          SECURITY            |         ACCESSIBILITY         |
|  p95 API < 300 ms (Read) |   OWASP Top 10 Hardened      |    WCAG 2.1 Level AA Ready    |
|  10k Concurrent Learners |   Stateless SimpleJWT + RBAC |    Screen Reader & Keyboard   |
|  1,000 req/sec Throughput|   GDPR Export & Erasure      |    Captions & Transcripts     |
+--------------------------+------------------------------+-------------------------------+
```

### `NFR-PERF-01`: API Response Latency Targets
- **Target Metric:**
  - Common Read Endpoints (Course catalog, lesson outline, user profile): **$p95 < 300\text{ ms}$** under standard production load.
  - Complex Write Endpoints (Enrollment creation, quiz submission, progress heartbeat): **$p95 < 500\text{ ms}$**.
  - Static Frontend Asset First Contentful Paint (FCP): **$< 1.2\text{ seconds}$**.
- **Validation Method:** Automated k6 / Locust load test script simulating continuous traffic profiles in Phase 8 ([`D-005`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-005-quantitative-non-functional-performance-targets)).
- **Justification:** Essential for fluid, responsive student interaction and minimizing bounce rates across international networks.

### `NFR-PERF-02`: High Concurrency & Scalability
- **Target Metric:** The platform architecture must support **10,000 concurrent active learners** generating up to **1,000 HTTP requests/second** without system crash or connection failure.
- **Validation Method:** Simulated concurrent user swarm executing read/write cycles against staging environment.
- **Justification:** Ensures platform resilience during peak examination periods or high-profile course launch events.

### `NFR-SCAL-01`: Stateless Horizontal Scalability
- **Target Metric:** Django web API nodes and Celery background workers must remain 100% stateless, allowing horizontal scaling behind a reverse proxy/load balancer without sticky sessions.
- **Validation Method:** Deployment validation with multiple backend replicas sharing Redis and Neon PostgreSQL.
- **Justification:** Permits elastic cost scaling and zero-downtime rolling updates.

### `NFR-AVAIL-01`: High Availability & Disaster Recovery
- **Target Metric:** **99.9% monthly availability** (maximum 43.8 minutes unplanned downtime per calendar month). Mean Time to Recover (MTTR) **$< 15\text{ minutes}$**.
- **Validation Method:** Documented and verified database point-in-time recovery and branch restore process in Neon.
- **Justification:** Protects academic continuity and prevents student assessment disruption.

### `NFR-SEC-01`: Comprehensive OWASP Top 10 Hardening
- **Target Metric:** Zero critical or high-severity vulnerabilities in automated dynamic and static application security testing (SAST/DAST).
  1. **SQL Injection:** 100% parameterization via Django ORM; raw SQL strictly forbidden.
  2. **Cross-Site Scripting (XSS):** React auto-escaping, DOMPurify sanitization on rich text, strict Content Security Policy (CSP).
  3. **Cross-Site Request Forgery (CSRF):** SameSite cookies and DRF token validation.
  4. **Rate Limiting:** IP-based and user-based throttling on authentication endpoints (5 attempts/min on login).
- **Validation Method:** Automated vulnerability scanners and unit security test cases.
- **Justification:** Safeguards sensitive student records, passwords, and intellectual property.

### `NFR-SEC-02`: Cryptographic Security & Secrets Handling
- **Target Metric:** All communication over HTTPS (TLS 1.3). Passwords hashed using PBKDF2 with SHA-256 (Django default, minimum 600,000 iterations). Secrets stored exclusively in environment variables, never committed to git.
- **Validation Method:** Pre-commit entropy and secret scanners (e.g., git-secrets) in CI pipeline.
- **Justification:** Industry-standard defense against credential compromise and credential stuffing attacks.

### `NFR-PRIV-01`: GDPR Compliance & Data Privacy Rights
- **Target Metric:** Full compliance with global privacy regulations:
  1. **Right to Access / Portability:** Self-service one-click export generating a machine-readable JSON archive of all learner records within 24 hours.
  2. **Right to Erasure ("Be Forgotten"):** Self-service account deletion request that permanently anonymizes student data in compliance with data retention laws.
- **Validation Method:** Unit tests verifying personal data erasure across `User`, `Enrollment`, `Progress`, and `QuizAttempt`.
- **Justification:** Legal prerequisite for operating an international educational service processing European and global learner data.

### `NFR-A11Y-01`: Universal Accessibility (WCAG 2.1 Level AA)
- **Target Metric:** 100% conformance with **WCAG 2.1 Level AA** across all learner-facing and authoring interfaces:
  1. Full keyboard operability (zero keyboard focus traps; visible focus indicators).
  2. Screen reader compatibility (semantic HTML5, descriptive ARIA attributes, form labels).
  3. Minimum contrast ratio of 4.5:1 for normal text and 3:1 for large text.
  4. Synchronized closed captions and transcripts for all video and audio content.
  5. User controls for high contrast mode, adjustable font sizing, and reduced motion preferences.
- **Validation Method:** Automated `@axe-core/playwright` CI test assertions and manual keyboard navigation audits.
- **Justification:** Fundamental institutional commitment ensuring learners with disabilities enjoy equal educational access.

### `NFR-COMP-01`: Cross-Browser & Device Compatibility
- **Target Metric:** Flawless rendering and operation on current stable versions of major browsers: Google Chrome, Mozilla Firefox, Apple Safari, Microsoft Edge, and Mobile Safari/Chrome on iOS and Android. Responsive layouts from 320px (mobile) to 4K desktop.
- **Validation Method:** Multi-browser Playwright matrix execution across Desktop and Mobile viewports.
- **Justification:** Students access distance education across diverse smartphones, tablets, and personal computers.

### `NFR-MAINT-01`: Modularity, Code Quality & Test Coverage
- **Target Metric:** Modular monolith architecture with strict domain boundaries (`apps/*`). Minimum **80% backend automated test coverage** on critical business services; zero linting warnings (Ruff/ESLint in strict mode).
- **Validation Method:** CI pipeline gate blocking PR merges if coverage drops below threshold.
- **Justification:** Directly satisfies course learning outcome CLO-3 and ensures rapid, maintainable feature iteration.

### `NFR-USAB-01`: Non-Technical Authoring Usability
- **Target Metric:** A non-technical content designer must be able to create a draft course, add a module, upload media, create a quiz, and publish the course within **15 minutes** without developer assistance, achieving a System Usability Scale (SUS) score **$\ge 80$**.
- **Validation Method:** Structured usability walkthrough evaluation against defined authoring tasks.
- **Justification:** Solves the core CCP operational constraint ("frequent content updates by non-technical staff").

### `NFR-LOC-01`: Internationalization & Localization Readiness
- **Target Metric:** UI architecture prepared for multi-language localization (i18n): all dates/times stored in UTC and rendered in user's local timezone; text strings extracted into key-value translation dictionaries; layout resilient to text expansion and Right-to-Left (RTL) reading directions.
- **Validation Method:** Automated visual regression tests verifying layout stability with long mock translations.
- **Justification:** Supports FutureLearning's planned expansion across global non-English-speaking markets.

---

## 7. Resolution of Ill-Defined & Ambiguous Requirements (Addressing CP-9)

In accordance with course attribute **CP-9 (Requirements Identification for Ill-Defined Problems)**, the initial project brief contained several ambiguous, high-level statements. The table below documents how each ambiguity was rigorously identified, analyzed, and resolved into concrete engineering specifications:

| Area of Ambiguity | Original Ambiguous Statement in Brief | Engineering Analysis & Options Evaluated | Chosen Concrete Specification & Resolution |
|---|---|---|---|
| **Adaptive Personalization** | *"Adaptive learning paths and personalized learning based on student progress."* | Option A: Complex deep learning recommendation model (requires massive training data not present in starter).<br>Option B: Purely static linear curriculum (fails CCP personal learning objective).<br>Option C: Explainable, rule-based knowledge-space model using skill graphs and threshold branching. | **Resolved via `D-004` & `FR-PER-01`–`05`:** Implemented a directed skill prerequisite graph with explicit mastery thresholds (< 70% remedial, ≥ 85% advanced). Encapsulated behind a pluggable `AdaptiveStrategy` interface. |
| **Simulations & Interactive Content** | *"Support interactive content and simulations."* | Option A: Build custom simulation engines in Django/React (unrealistic scope).<br>Option B: Link to external websites (loses learner state).<br>Option C: Sandboxed `<iframe>` embed with standardized bi-directional `postMessage` contract for secure score reporting. | **Resolved via `D-004` & `FR-SIM-01`–`03`:** Standardized sandboxed iframe protocol (`SIM_INIT`, `SIM_SCORE_REPORT`) allowing any HTML5 widget to safely communicate telemetry to the LMS. |
| **Media Storage Architecture** | *"Support video, audio, and documents."* | Option A: Store binaries in PostgreSQL database (causes severe bloat and Neon connection exhaustion).<br>Option B: Proxy uploads through Django web workers (starves web threads).<br>Option C: Provider-agnostic S3 storage via presigned browser uploads. | **Resolved via `D-003` & `FR-MED-01`:** Large media uploaded directly to bucket via presigned URLs. Neon stores only metadata (`MediaAsset`), thumbnail keys, and caption URLs. |
| **Assessment Attempt Rules** | *"Quizzes and progress tracking."* | Option A: Hardcoded unlimited attempts (encourages brute force).<br>Option B: Hardcoded single attempt (too punitive for practice).<br>Option C: Instructor-configured attempt limits with high-water mark scoring. | **Resolved via `D-004` & `FR-ASM-01`–`03`:** Instructors explicitly define `max_attempts` per quiz. The platform enforces this limit on the server and preserves the highest score achieved. |
| **Course Progress Invariants** | *"Student progress tracking."* | Option A: Client tells server progress percentage (vulnerable to spoofing).<br>Option B: Track only coarse course completion.<br>Option C: Server-calculated progress derived from verified lesson completion events with idempotent updates. | **Resolved via `FR-TRK-01`–`02`:** Server computes completion mathematically from required lessons. Progress heartbeats are debounced and processed idempotently to prevent race conditions. |
| **Monetization vs. Academic Scope** | *"Platform delivering online education across diverse subjects."* | Option A: Integrate Stripe/PayPal payment gateway (adds billing overhead outside core educational CCP).<br>Option B: Free-to-access academic model with modular enrollment gates. | **Resolved via `docs/00-workspace-analysis.md`:** All courses in the MVP are free-to-access. Payment processing is explicitly documented as Out-of-Scope (MoSCoW Won't Have). |

---

## 8. Assumptions, Constraints, & Out-of-Scope Boundaries

### 8.1 Key Project Assumptions
- **A-01 (Audience Infrastructure):** Learners have access to a modern web browser supporting ES2022+ and WebAssembly, with at least a 256 kbps internet connection for low-bandwidth modes.
- **A-02 (Team & Resource Model):** Built under university software engineering constraints by a 4-person student engineering team across a 12-week academic semester lifecycle ([`D-004`](file:///c:/Users/amtul/Desktop/futurelearning_starter/docs/decision.md#d-004-user-scope-clarifications-and-operational-parameters)).
- **A-03 (Hosting Infrastructure):** Primary relational data is hosted on Neon Serverless PostgreSQL; media binaries reside in an S3-compatible bucket; caching and queues run on Redis and Celery.
- **A-04 (Content Authority):** Content designers are trusted institutional educators; primary moderation focuses on student-generated discussion forums.

### 8.2 Technical & Operational Constraints
- **C-01 (Database Single-Point Entry):** Django is the sole software component authorized to connect to Neon PostgreSQL. The browser and frontend must never receive direct database connection credentials.
- **C-02 (Separation of Storage):** No video, audio, or PDF file bytes may be persisted inside PostgreSQL tables; only metadata keys and URLs are permitted.
- **C-03 (Strict Accessibility):** Every user journey must pass automated and manual WCAG 2.1 AA keyboard and contrast audits.
- **C-04 (No Direct Server Migrations on Pooled Neon):** Schema migrations must utilize direct connections or branch migrations to prevent Neon connection pool locking.

### 8.3 Out-of-Scope Boundary (MoSCoW Won't Have for Current Scope)
To ensure project delivery within schedule constraints, the following capabilities are explicitly deferred:
- **W-01: Payment Gateway & E-Commerce Subscriptions:** The MVP operates as an open-access platform. Paid checkout workflows and billing invoices are deferred.
- **W-02: Native Mobile Applications (iOS/Android):** Delivery is achieved through a responsive Next.js Progressive Web App (PWA); native Swift/Kotlin codebases are out of scope.
- **W-03: Real-Time WebRTC Video Conferencing:** Live virtual classrooms are deferred; learning is delivered asynchronously.
- **W-04: Complex Black-Box Machine Learning Models:** Initial adaptive pathways use explainable rule-based heuristics; opaque deep learning models are deferred.
- **W-05: SCORM / xAPI / LTI Enterprise Import Tools:** External legacy LMS packaging tools are out of scope.
- **W-06: Microservices Orchestration (Kubernetes/Istio):** The platform is purposefully designed as a modular monolith to maximize development velocity and prevent distributed systems overhead.

---

## 9. Requirements Traceability Baseline Summary

- **Total Functional Requirements:** 47 (`FR-AUTH-01` to `FR-ADM-04`)
- **Total Non-Functional Requirements:** 12 (`NFR-PERF-01` to `NFR-LOC-01`)
- **Total Strategic Goals:** 8 (`G-01` to `G-08`)
- **Traceability Guarantee:** In subsequent phases, every system design component (`docs/02-system-design.md`), code module (`backend/apps/*`, `frontend/src/*`), and test case (`docs/03-test-plan.md`) will reference these exact requirement IDs.
