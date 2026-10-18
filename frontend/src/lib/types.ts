export type UserRole = "GUEST" | "LEARNER" | "INSTRUCTOR" | "MODERATOR" | "ADMIN";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  role: UserRole;
  is_email_verified: boolean;
  avatar?: string | null;
  bio?: string;
  preferred_language?: string;
  terms_accepted: boolean;
  privacy_accepted: boolean;
  marketing_consent: boolean;
  date_joined?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: User;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  course_count?: number;
}

export type CourseDifficulty = "BEGINNER" | "INTERMEDIATE" | "ADVANCED" | "ALL_LEVELS";
export type CourseStatus = "DRAFT" | "IN_REVIEW" | "PUBLISHED" | "ARCHIVED";

export interface Course {
  id: string;
  slug: string;
  title: string;
  short_description?: string;
  description: string;
  thumbnail_url?: string | null;
  difficulty: CourseDifficulty;
  status: CourseStatus;
  estimated_duration_minutes: number;
  version: number;
  module_count?: number;
  instructor: {
    id: string;
    name: string;
    email: string;
    avatar?: string | null;
    bio?: string;
  };
  category?: Category | null;
  modules?: Module[];
  is_enrolled?: boolean;
  created_at?: string;
  published_at?: string | null;
}

export interface Module {
  id: string;
  course?: string;
  title: string;
  description?: string;
  position: number;
  lessons: Lesson[];
  created_at?: string;
}

export interface Lesson {
  id: string;
  module?: string;
  title: string;
  slug: string;
  position: number;
  estimated_duration_minutes: number;
  is_required: boolean;
  is_preview: boolean;
  is_published: boolean;
  content_blocks?: ContentBlock[];
}

export type ContentBlockType = "TEXT" | "VIDEO" | "AUDIO" | "PDF" | "SIMULATION" | "QUIZ_REF";

export interface ContentBlock {
  id: string;
  lesson: string;
  block_type: ContentBlockType;
  title?: string;
  position: number;
  content_payload: {
    markdown?: string;
    html?: string;
    sim_url?: string;
    sandbox_flags?: string;
    download_url?: string;
    storage_key?: string;
    stream_url?: string;
    captions?: string;
    transcript?: string;
    quiz_id?: string;
    [key: string]: any;
  };
  media_asset?: string | null;
  media_asset_details?: MediaAsset | null;
  is_draft: boolean;
  version: number;
  created_at?: string;
}

export interface MediaAsset {
  id: string;
  storage_key: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  duration_seconds: number;
  thumbnail_key?: string;
  transcript_url?: string;
  captions_url?: string;
  status: "PENDING" | "PROCESSING" | "READY" | "REJECTED";
  download_url?: string;
}

export interface Enrollment {
  id: string;
  course: Course;
  status: "ACTIVE" | "COMPLETED" | "DROPPED";
  enrolled_at: string;
  completed_at?: string | null;
}

export interface PresignedUploadTicket {
  upload_url: string;
  storage_key: string;
  storage_provider: string;
  method: string;
  headers: Record<string, string>;
}

export type LessonProgressStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";

export interface LessonProgress {
  id: string;
  lesson: {
    id: string;
    title: string;
    slug: string;
    position: number;
    estimated_duration_minutes: number;
    is_required: boolean;
    is_preview: boolean;
  };
  status: LessonProgressStatus;
  completion_percent: number;
  last_position_seconds: number;
  completed_at?: string | null;
  updated_at: string;
}

export interface CourseProgressDetail {
  course_id: string;
  course_title: string;
  course_slug: string;
  enrollment_status: "ACTIVE" | "COMPLETED" | "DROPPED";
  total_required_lessons: number;
  completed_lessons: number;
  completion_percent: number;
  is_completed: boolean;
  completed_at?: string | null;
  last_active_lesson?: {
    lesson_id: string;
    title: string;
    slug: string;
    last_position_seconds: number;
    status: LessonProgressStatus;
  } | null;
  lessons: LessonProgress[];
}

export interface HeartbeatPayload {
  lesson_id: string;
  position_seconds: number;
  completion_percent: number;
  is_completed?: boolean;
}

export interface HeartbeatResponse {
  status: string;
  lesson_id: string;
  lesson_status: LessonProgressStatus;
  lesson_completion_percent: number;
  last_position_seconds: number;
  course_completion_percent: number;
  is_course_completed: boolean;
}

export interface Skill {
  id: string;
  name: string;
  slug: string;
  description: string;
  mastery_score?: number;
  prerequisites: Array<{ id: string; name: string; slug?: string }>;
}

export interface StudentSkill {
  id: string;
  skill: Skill;
  mastery_score: number;
  updated_at: string;
}

export type PathType = "STANDARD" | "REMEDIATION" | "ENRICHMENT";

export interface LearningPathItem {
  id: string;
  position: number;
  path_type: PathType;
  reason: string;
  is_completed: boolean;
  lesson: {
    id: string;
    title: string;
    slug: string;
    position: number;
    estimated_duration_minutes: number;
    is_required: boolean;
    is_preview: boolean;
  };
}

export interface LearningPath {
  id: string;
  course_id: string;
  course_title: string;
  course_slug: string;
  status: "ACTIVE" | "COMPLETED" | "ARCHIVED";
  generated_at: string;
  items: LearningPathItem[];
}

// ==========================================
// Phase 7: Interactive Features Types
// ==========================================

export type QuestionType =
  | "SINGLE_CHOICE"
  | "MULTIPLE_CHOICE"
  | "TRUE_FALSE"
  | "SHORT_ANSWER"
  | "CODE_SNIPPET";

export interface Choice {
  id: string;
  text: string;
  position: number;
  feedback?: string;
}

export interface Question {
  id: string;
  question_type: QuestionType;
  prompt: string;
  points: number;
  position: number;
  code_language?: string;
  initial_code?: string;
  choices: Choice[];
}

export interface Assessment {
  id: string;
  course: string;
  lesson?: string | null;
  title: string;
  description: string;
  passing_score_percent: number;
  time_limit_minutes: number;
  max_attempts: number;
  is_published: boolean;
  questions: Question[];
  attempts_used: number;
  attempts_remaining: number;
  highest_score: number;
  has_passed: boolean;
}

export interface QuizAttempt {
  id: string;
  assessment: string;
  attempt_number: number;
  status: "IN_PROGRESS" | "SUBMITTED" | "TIMED_OUT" | "ABANDONED";
  started_at: string;
  submitted_at?: string | null;
  score_percent: number;
  points_earned: number;
  points_possible: number;
  passed: boolean;
}

export interface QuestionGradeResult {
  question_id: string;
  prompt: string;
  question_type: QuestionType;
  points_possible: number;
  awarded_points: number;
  is_correct: boolean;
  explanation: string;
  feedback?: string;
  selected_choices: string[];
  text_response?: string;
  correct_choices: Array<{ id: string; text: string }>;
}

export interface GradeSummary {
  attempt_id: string;
  assessment_id: string;
  assessment_title: string;
  attempt_number: number;
  max_attempts: number;
  attempts_remaining: number;
  status: string;
  score_percent: number;
  points_earned: number;
  points_possible: number;
  passing_score_percent: number;
  passed: boolean;
  submitted_at: string | null;
  questions: QuestionGradeResult[];
}

export interface DiscussionThread {
  id: string;
  course: string;
  lesson?: string | null;
  author: User;
  title: string;
  body: string;
  status: "ACTIVE" | "PINNED" | "LOCKED" | "HIDDEN";
  is_pinned: boolean;
  upvotes_count: number;
  views_count: number;
  replies_count: number;
  has_upvoted: boolean;
  created_at: string;
  updated_at: string;
  posts?: DiscussionPost[];
}

export interface DiscussionPost {
  id: string;
  thread: string;
  author: User;
  parent?: string | null;
  body: string;
  is_endorsed: boolean;
  endorsed_by?: User | null;
  endorsed_at?: string | null;
  status: "ACTIVE" | "HIDDEN" | "FLAGGED";
  upvotes_count: number;
  has_upvoted: boolean;
  replies?: DiscussionPost[];
  created_at: string;
  updated_at: string;
}

export interface ContentReport {
  id: string;
  reporter: User;
  thread?: string | null;
  post?: string | null;
  reason: string;
  details?: string;
  status: "PENDING" | "RESOLVED" | "DISMISSED";
  created_at: string;
  resolved_at?: string | null;
}

export interface Notification {
  id: string;
  notification_type:
    | "FORUM_REPLY"
    | "ANSWER_ENDORSED"
    | "ASSESSMENT_GRADED"
    | "COURSE_ANNOUNCEMENT"
    | "REPORT_RESOLVED"
    | "SIMULATION_MILESTONE";
  title: string;
  message: string;
  action_url?: string;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

// ==========================================
// Phase 8: Analytics & Privacy Types (FR-ANL-01 to 03, FR-PRV-01 & 02)
// ==========================================

export interface DifficultQuestionMetric {
  question_id: string;
  prompt: string;
  total_attempts: number;
  pass_rate_percent: number;
}

export interface DropOffFunnelItem {
  lesson_id: string;
  title: string;
  module_title: string;
  completed_count: number;
  completion_percent_of_enrolled: number;
}

export interface InstructorAnalytics {
  course_id: string;
  course_title: string;
  course_slug: string;
  total_enrolled: number;
  active_students_14d: number;
  completed_students: number;
  completion_rate_percent: number;
  avg_quiz_score_percent: number;
  total_forum_threads: number;
  difficult_questions: DifficultQuestionMetric[];
  drop_off_curve: DropOffFunnelItem[];
  last_computed_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor_email?: string;
  action: string;
  target_model: string;
  target_id: string;
  ip_hash?: string;
  changes?: Record<string, any>;
  timestamp: string;
}

export interface AdminPlatformOverview {
  total_users: number;
  users_by_role: Record<string, number>;
  active_users_30d: number;
  total_courses: number;
  published_courses: number;
  total_enrollments: number;
  completed_enrollments: number;
  platform_completion_rate: number;
  estimated_learning_hours: number;
  recent_audit_logs: AuditLogEntry[];
  last_computed_at: string;
}

export interface LearnerEngagementSummary {
  total_enrolled_courses: number;
  in_progress_courses: number;
  completed_courses: number;
  completed_lessons_count: number;
  total_learning_minutes: number;
  active_streak_days: number;
  quiz_attempts_count: number;
  quizzes_passed_count: number;
  member_since: string | null;
}


