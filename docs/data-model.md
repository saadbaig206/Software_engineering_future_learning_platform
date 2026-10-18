# Data Model / Database Schema — Neon PostgreSQL

## Conventions
- PostgreSQL is the source of truth; Django models and migrations own schema changes.
- Primary keys: UUIDs are proposed for public-facing entities to reduce ID enumeration. Django's built-in auth model uses its own compatible primary key configuration as set in the implementation.
- All timestamps are stored timezone-aware in UTC.
- Every model should define indexes/constraints based on query patterns.
- This is the logical schema. Field lengths and constraints should be refined during implementation.

## Entities

### User
Identity and authorization. Use a custom Django user model before first migration.
- id (PK)
- email (unique, login identifier)
- password_hash (managed by Django)
- first_name, last_name
- role (`LEARNER`, `INSTRUCTOR`, `ADMIN`) — proposed
- is_active, is_staff, date_joined

### Category
- id (PK), name, slug (unique), description

### Course
- id (PK), instructor_id (FK User), category_id (FK Category, nullable)
- title, slug, short_description, description, thumbnail_url
- difficulty (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`)
- status (`DRAFT`, `IN_REVIEW`, `PUBLISHED`, `ARCHIVED`)
- estimated_duration_minutes, published_at, created_at, updated_at
- Index: status + category; slug unique

### Module
- id (PK), course_id (FK Course), title, description, position, created_at, updated_at
- Unique constraint: (course_id, position)

### Lesson
- id (PK), module_id (FK Module), title, description, content_type
- text_content (nullable), media_asset_id (FK MediaAsset, nullable)
- position, duration_seconds, is_required, is_preview, is_published
- created_at, updated_at
- Unique constraint: (module_id, position)
- Content types: `TEXT`, `VIDEO`, `AUDIO`, `DOCUMENT`, `QUIZ`, `INTERACTIVE`

### MediaAsset
- id (PK), uploaded_by_id (FK User)
- storage_key, original_filename, mime_type, size_bytes, duration_seconds (nullable)
- alt_text, transcript_url, captions_url, created_at
- Store object-storage key/URL metadata, not the actual large file in PostgreSQL.

### Enrollment
- id (PK), learner_id (FK User), course_id (FK Course)
- status (`ACTIVE`, `COMPLETED`, `CANCELLED`)
- enrolled_at, completed_at, last_accessed_at
- Unique constraint: (learner_id, course_id)

### LessonProgress
- id (PK), enrollment_id (FK Enrollment), lesson_id (FK Lesson)
- status (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`)
- completion_percent (0–100), last_position_seconds
- started_at, completed_at, updated_at
- Unique constraint: (enrollment_id, lesson_id)
- Validate lesson belongs to enrollment's course through its module/course relationship.

### Assessment
- id (PK), lesson_id (one-to-one FK Lesson)
- title, instructions, passing_score_percent, time_limit_seconds (nullable), max_attempts (nullable), is_published
- created_at, updated_at

### Question
- id (PK), assessment_id (FK Assessment)
- question_type (`SINGLE_CHOICE`, `MULTIPLE_SELECT`, `TRUE_FALSE`, `SHORT_ANSWER`)
- prompt, points, position, explanation (nullable)
- Unique constraint: (assessment_id, position)

### Choice
- id (PK), question_id (FK Question), text, position, is_correct
- Unique constraint: (question_id, position)
- Security: do not expose `is_correct` in learner question payload before submission.

### QuizAttempt
- id (PK), assessment_id (FK Assessment), enrollment_id (FK Enrollment)
- attempt_number, status (`IN_PROGRESS`, `SUBMITTED`, `GRADED`)
- started_at, submitted_at, score_percent, passed
- Unique constraint: (enrollment_id, assessment_id, attempt_number)

### Answer
- id (PK), attempt_id (FK QuizAttempt), question_id (FK Question)
- selected_choice_ids (implementation option: normalized AnswerChoice join table recommended for multi-select)
- text_answer, awarded_points, is_correct
- Unique constraint: (attempt_id, question_id)

### AnswerChoice (recommended normalization)
- id (PK), answer_id (FK Answer), choice_id (FK Choice)
- Unique constraint: (answer_id, choice_id)

### LearningProfile
- id (PK), learner_id (one-to-one FK User)
- preferred_content_type (nullable), preferred_pace (nullable)
- created_at, updated_at
- Keep only data that has a clear product purpose and user-facing explanation.

### Skill
- id (PK), name, slug (unique), description

### LessonSkill
- id (PK), lesson_id (FK Lesson), skill_id (FK Skill), contribution_weight
- Unique constraint: (lesson_id, skill_id)

### StudentSkill
- id (PK), learner_id (FK User), skill_id (FK Skill)
- mastery_score (0–100), updated_at
- Unique constraint: (learner_id, skill_id)

### LearningPath
- id (PK), learner_id (FK User), course_id (FK Course, nullable)
- status (`ACTIVE`, `COMPLETED`, `ARCHIVED`), generated_at, updated_at

### LearningPathItem
- id (PK), learning_path_id (FK LearningPath), lesson_id (FK Lesson)
- position, reason, status (`RECOMMENDED`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`)
- Unique constraint: (learning_path_id, position)

### DiscussionThread
- id (PK), course_id (FK Course), lesson_id (FK Lesson, nullable)
- author_id (FK User), title, body, status (`VISIBLE`, `HIDDEN`, `LOCKED`)
- created_at, updated_at

### DiscussionPost
- id (PK), thread_id (FK DiscussionThread), author_id (FK User)
- parent_id (self FK, nullable), body, status, created_at, updated_at

### Notification (P2)
- id (PK), recipient_id (FK User), type, title, message, read_at (nullable), created_at

### LearningEvent (optional analytics event log)
- id (PK), learner_id (FK User, nullable for anonymized system events)
- event_type, course_id (nullable FK), lesson_id (nullable FK)
- metadata JSONB, created_at
- Add retention/aggregation rules before production; avoid storing sensitive free text in metadata.

## Relationship summary
- User 1—many Course (as instructor)
- Category 1—many Course
- Course 1—many Module 1—many Lesson
- User 1—many Enrollment; Course 1—many Enrollment
- Enrollment 1—many LessonProgress
- Lesson 0—1 Assessment; Assessment 1—many Question 1—many Choice
- Enrollment 1—many QuizAttempt; QuizAttempt 1—many Answer
- User 1—1 LearningProfile; User many-to-many Skill through StudentSkill
- Lesson many-to-many Skill through LessonSkill
- User 1—many LearningPath; LearningPath 1—many LearningPathItem
- Course 1—many DiscussionThread; Thread 1—many DiscussionPost; posts can reply to posts
