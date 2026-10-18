# REST API Specification (proposed v1)

Base path: `/api/v1/`. JSON unless stated otherwise. This is a contract proposal; exact pagination/error formats should be standardized during implementation. Authentication is required except where noted.

## Conventions
- Use plural resources and trailing slashes to match Django conventions.
- Use `GET` for reads, `POST` for create/actions, `PATCH` for partial updates, and `DELETE` where deletion is permitted.
- Use server-side role/resource permissions for every write and protected read.
- List endpoints should be paginated and support stable ordering.
- Suggested error shape: `{"detail":"Human-readable error","code":"permission_denied"}`; validation errors may include field-level details.
- IDs are opaque strings (UUIDs recommended).
- Never include `Choice.is_correct` in learner assessment payloads before grading.

## Authentication
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| POST | `/auth/register/` | Register learner | Public |
| POST | `/auth/login/` | Authenticate | Public |
| POST | `/auth/refresh/` | Refresh access token/session | Auth strategy dependent |
| POST | `/auth/logout/` | Logout/revoke refresh token if supported | Authenticated |
| GET | `/auth/me/` | Current profile and role | Authenticated |

Implementation note: choose either secure cookie-based session auth or JWT with refresh rotation and a safe browser storage strategy. Do not place long-lived tokens in localStorage without a documented threat analysis.

## Catalogue and courses
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/courses/` | List published courses; filters: search, category, difficulty | Public |
| POST | `/courses/` | Create draft course | Instructor/Admin |
| GET | `/courses/{course_id}/` | Course detail | Public if published; owner/admin can preview draft |
| PATCH | `/courses/{course_id}/` | Update course metadata | Owner/Admin |
| POST | `/courses/{course_id}/publish/` | Publish after validation | Owner/Admin |
| POST | `/courses/{course_id}/archive/` | Archive course | Owner/Admin |
| GET | `/categories/` | List categories | Public |

## Modules and lessons
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/courses/{course_id}/modules/` | Ordered modules | Public published course or authorized preview |
| POST | `/courses/{course_id}/modules/` | Add module | Owner/Admin |
| PATCH | `/modules/{module_id}/` | Update/reorder module | Owner/Admin |
| DELETE | `/modules/{module_id}/` | Delete module if safe | Owner/Admin |
| GET | `/modules/{module_id}/lessons/` | Ordered lessons | Published/enrolled or owner/admin |
| POST | `/modules/{module_id}/lessons/` | Add lesson | Owner/Admin |
| GET | `/lessons/{lesson_id}/` | Lesson detail | Preview, enrolled learner, or owner/admin |
| PATCH | `/lessons/{lesson_id}/` | Update lesson | Owner/Admin |
| POST | `/lessons/{lesson_id}/media-upload-url/` | Obtain short-lived upload URL (future storage integration) | Owner/Admin |

## Enrollment and progress
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| POST | `/courses/{course_id}/enroll/` | Enroll current learner | Learner |
| GET | `/me/enrollments/` | List own enrollments | Learner |
| GET | `/enrollments/{enrollment_id}/` | Enrollment details | Owner/Admin |
| POST | `/lessons/{lesson_id}/start/` | Start/resume lesson | Enrolled learner |
| PATCH | `/lessons/{lesson_id}/progress/` | Save completion percent/media position | Enrolled learner |
| POST | `/lessons/{lesson_id}/complete/` | Mark complete after server validation | Enrolled learner |
| GET | `/me/progress/` | Own course/lesson progress | Learner |
| GET | `/courses/{course_id}/progress-summary/` | Aggregate progress | Course owner/Admin; privacy-aware |

## Assessments
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| POST | `/lessons/{lesson_id}/assessment/` | Create assessment | Owner/Admin |
| GET | `/assessments/{assessment_id}/` | Get learner-safe assessment | Enrolled learner or owner/admin |
| POST | `/assessments/{assessment_id}/attempts/` | Start attempt | Enrolled learner |
| POST | `/attempts/{attempt_id}/submit/` | Submit answers; server grades | Attempt owner |
| GET | `/attempts/{attempt_id}/result/` | View result and permitted feedback | Attempt owner; owner/admin summary rules apply |

## Personalization
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/me/skills/` | Own mastery scores | Learner |
| GET | `/me/recommendations/` | Recommendations with reason | Learner |
| GET | `/me/learning-path/` | Active ordered path | Learner |
| POST | `/me/learning-path/regenerate/` | Recompute path | Learner; rate-limited |

## Discussions
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/courses/{course_id}/discussions/` | List threads | Published/enrolled policy |
| POST | `/courses/{course_id}/discussions/` | Create thread | Enrolled learner/instructor |
| GET | `/discussions/{thread_id}/` | Thread and replies | Authorized participant |
| POST | `/discussions/{thread_id}/posts/` | Reply | Authorized participant |
| POST | `/discussions/{thread_id}/report/` | Report content | Authenticated |
| POST | `/discussions/{thread_id}/moderate/` | Hide/lock thread | Moderator/Admin |

## Analytics and admin
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/instructor/overview/` | Instructor-owned course summary | Instructor |
| GET | `/courses/{course_id}/analytics/` | Enrollment, completion, quiz and drop-off metrics | Owner/Admin |
| GET | `/admin/users/` | User management list | Admin |
| PATCH | `/admin/users/{user_id}/` | Update active/role state | Admin |
| GET | `/notifications/` | Own notifications (later phase) | Authenticated |
| PATCH | `/notifications/{notification_id}/read/` | Mark read (later phase) | Recipient |

## Example response: course list item
```json
{
  "id": "uuid",
  "title": "Introduction to Python",
  "slug": "introduction-to-python",
  "short_description": "Learn programming fundamentals.",
  "difficulty": "BEGINNER",
  "estimated_duration_minutes": 240,
  "instructor": {"id": "uuid", "display_name": "Instructor"},
  "published_at": "2026-10-17T10:00:00Z"
}
```

## Example response: recommendation
```json
{
  "lesson_id": "uuid",
  "title": "Loops: guided revision",
  "reason": "Your recent loops assessment was below the configured mastery threshold.",
  "priority": 0.82,
  "recommendation_type": "REVISION"
}
```

## Cross-cutting implementation rules
- Use transactions for quiz submission and other multi-table domain operations.
- Add idempotency or safe repeated-request behavior to progress/completion actions.
- Validate ownership and enrollment in querysets/services, not just serializer fields.
- Return 401 for unauthenticated requests and 403 for authenticated users lacking permission, unless deliberately using a non-disclosing 404 policy.
- Document pagination, filtering, sorting, throttling, and error responses in OpenAPI.
