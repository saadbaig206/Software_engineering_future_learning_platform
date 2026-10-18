import axios from "axios";
import {
  Assessment,
  AuthTokens,
  Category,
  ContentBlock,
  ContentReport,
  Course,
  CourseProgressDetail,
  DiscussionPost,
  DiscussionThread,
  Enrollment,
  GradeSummary,
  HeartbeatPayload,
  HeartbeatResponse,
  LearningPath,
  Lesson,
  Module,
  Notification,
  PresignedUploadTicket,
  QuizAttempt,
  Skill,
  StudentSkill,
  User,
  InstructorAnalytics,
  AdminPlatformOverview,
  LearnerEngagementSummary,
  AuditLogEntry,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Request interceptor to attach JWT Bearer token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("fl_access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token renewal or 401 unauth
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      if (typeof window !== "undefined") {
        const refresh = localStorage.getItem("fl_refresh_token");
        if (refresh) {
          try {
            const res = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
              refresh,
            });
            const newAccess = res.data.access;
            const newRefresh = res.data.refresh;
            localStorage.setItem("fl_access_token", newAccess);
            if (newRefresh) localStorage.setItem("fl_refresh_token", newRefresh);
            originalRequest.headers.Authorization = `Bearer ${newAccess}`;
            return apiClient(originalRequest);
          } catch (e) {
            localStorage.removeItem("fl_access_token");
            localStorage.removeItem("fl_refresh_token");
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

// ==========================================
// Authentication & User APIs
// ==========================================
export async function loginUser(credentials: {
  email: string;
  password: string;
}): Promise<AuthTokens> {
  const response = await apiClient.post<AuthTokens>("/auth/token/", credentials);
  return response.data;
}

export async function registerUser(payload: {
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  role?: string;
  terms_accepted: boolean;
  privacy_accepted: boolean;
  marketing_consent?: boolean;
}): Promise<{ message: string; user: User; verification_token?: string }> {
  const response = await apiClient.post("/auth/register/", payload);
  return response.data;
}

export async function verifyEmail(token: string): Promise<{ message: string }> {
  const response = await apiClient.post("/auth/verify-email/", { token });
  return response.data;
}

export async function getUserProfile(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me/");
  return response.data;
}

export async function updateUserProfile(data: Partial<User>): Promise<User> {
  const response = await apiClient.patch<User>("/auth/me/", data);
  return response.data;
}

// ==========================================
// Courses & Catalog APIs
// ==========================================
export interface CourseFilterParams {
  category?: string;
  difficulty?: string;
  search?: string;
  my_courses?: boolean;
}

export async function getCourses(params?: CourseFilterParams): Promise<Course[]> {
  const response = await apiClient.get<{ results: Course[] } | Course[]>("/courses/", {
    params: {
      ...params,
      my_courses: params?.my_courses ? "true" : undefined,
    },
  });
  if (Array.isArray(response.data)) {
    return response.data;
  }
  return response.data.results || [];
}

export async function getCourseBySlug(slug: string): Promise<Course> {
  const response = await apiClient.get<Course>(`/courses/${slug}/`);
  return response.data;
}

export async function getCourseSyllabus(slug: string): Promise<Course> {
  const response = await apiClient.get<Course>(`/courses/${slug}/syllabus/`);
  return response.data;
}

export async function createCourse(payload: {
  title: string;
  description: string;
  short_description?: string;
  category?: string | null;
  difficulty?: string;
  thumbnail_url?: string;
  estimated_duration_minutes?: number;
}): Promise<Course> {
  const response = await apiClient.post<Course>("/courses/", payload);
  return response.data;
}

export async function updateCourse(
  slug: string,
  payload: Partial<Course>
): Promise<Course> {
  const response = await apiClient.patch<Course>(`/courses/${slug}/`, payload);
  return response.data;
}

export async function publishCourse(
  slug: string
): Promise<{ message: string; status: string }> {
  const response = await apiClient.post(`/courses/${slug}/publish/`);
  return response.data;
}

export async function archiveCourse(
  slug: string
): Promise<{ message: string; status: string }> {
  const response = await apiClient.post(`/courses/${slug}/archive/`);
  return response.data;
}

export async function enrollInCourse(
  slug: string
): Promise<{ message: string; enrollment_id: string; status: string }> {
  const response = await apiClient.post(`/courses/${slug}/enroll/`);
  return response.data;
}

export async function getMyEnrollments(): Promise<Enrollment[]> {
  const response = await apiClient.get<{ results: Enrollment[] } | Enrollment[]>(
    "/enrollments/"
  );
  if (Array.isArray(response.data)) {
    return response.data;
  }
  return response.data.results || [];
}

export async function getCategories(): Promise<Category[]> {
  const response = await apiClient.get<{ results: Category[] } | Category[]>(
    "/categories/"
  );
  if (Array.isArray(response.data)) {
    return response.data;
  }
  return response.data.results || [];
}

// ==========================================
// Modules & Lessons APIs
// ==========================================
export async function createModule(payload: {
  course: string;
  title: string;
  description?: string;
  position: number;
}): Promise<Module> {
  const response = await apiClient.post<Module>("/modules/", payload);
  return response.data;
}

export async function updateModule(
  id: string,
  payload: Partial<Module>
): Promise<Module> {
  const response = await apiClient.patch<Module>(`/modules/${id}/`, payload);
  return response.data;
}

export async function deleteModule(id: string): Promise<void> {
  await apiClient.delete(`/modules/${id}/`);
}

export async function createLesson(payload: {
  module: string;
  title: string;
  position: number;
  estimated_duration_minutes?: number;
  is_preview?: boolean;
  is_published?: boolean;
}): Promise<Lesson> {
  const response = await apiClient.post<Lesson>("/lessons/", payload);
  return response.data;
}

export async function updateLesson(
  id: string,
  payload: Partial<Lesson>
): Promise<Lesson> {
  const response = await apiClient.patch<Lesson>(`/lessons/${id}/`, payload);
  return response.data;
}

export async function deleteLesson(id: string): Promise<void> {
  await apiClient.delete(`/lessons/${id}/`);
}

// ==========================================
// Content Blocks & Media Upload APIs
// ==========================================
export async function getContentBlocks(lessonId: string): Promise<ContentBlock[]> {
  const response = await apiClient.get<
    { results: ContentBlock[] } | ContentBlock[]
  >("/content/blocks/", {
    params: { lesson_id: lessonId },
  });
  if (Array.isArray(response.data)) {
    return response.data;
  }
  return response.data.results || [];
}

export async function createContentBlock(
  payload: Partial<ContentBlock>
): Promise<ContentBlock> {
  const response = await apiClient.post<ContentBlock>("/content/blocks/", payload);
  return response.data;
}

export async function updateContentBlock(
  id: string,
  payload: Partial<ContentBlock>
): Promise<ContentBlock> {
  const response = await apiClient.patch<ContentBlock>(
    `/content/blocks/${id}/`,
    payload
  );
  return response.data;
}

export async function deleteContentBlock(id: string): Promise<void> {
  await apiClient.delete(`/content/blocks/${id}/`);
}

export async function getPresignedUploadUrl(
  lessonId: string | null,
  fileInfo: { filename: string; mime_type: string; size_bytes: number }
): Promise<PresignedUploadTicket> {
  const endpoint = lessonId
    ? `/content/lessons/${lessonId}/media-upload-url/`
    : "/content/media/upload-url/";
  const response = await apiClient.post<PresignedUploadTicket>(endpoint, fileInfo);
  return response.data;
}

export async function confirmMediaUpload(data: {
  storage_key: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
}): Promise<{ message: string; media_asset_id: string; status: string }> {
  const response = await apiClient.post("/content/media-assets/confirm/", data);
  return response.data;
}

export async function uploadFileDirectToStorage(
  ticket: PresignedUploadTicket,
  file: File,
  onProgress?: (progressPercent: number) => void
): Promise<void> {
  await axios.put(ticket.upload_url, file, {
    headers: ticket.headers,
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
}

// ==========================================
// Health & Smoke Testing APIs
// ==========================================
export interface SubsystemStatus {
  status: "ok" | "warning" | "error" | "unknown";
  message?: string;
  latency_ms?: number;
  backend?: string;
}

export interface HealthCheckResponse {
  status: "healthy" | "degraded";
  timestamp: number;
  services: {
    django: SubsystemStatus;
    database: SubsystemStatus;
    cache: SubsystemStatus;
    celery: SubsystemStatus;
  };
}

export interface SmokeTestPipelineResult {
  status: "SUCCESS" | "FAILED";
  message?: string;
  database_name?: string;
  engine_version?: string;
  key_tested?: string;
  verified?: boolean;
  task_id?: string;
}

export interface SmokeTestResponse {
  test_name: string;
  timestamp: number;
  total_elapsed_ms: number;
  all_passed: boolean;
  pipeline: {
    "1_django_api": SmokeTestPipelineResult;
    "2_neon_postgres": SmokeTestPipelineResult;
    "3_redis_cache": SmokeTestPipelineResult;
    "4_celery_task": SmokeTestPipelineResult;
  };
}

export async function getHealthCheck(): Promise<HealthCheckResponse> {
  const response = await apiClient.get<HealthCheckResponse>("/health/");
  return response.data;
}

export async function getSmokeTest(): Promise<SmokeTestResponse> {
  const response = await apiClient.get<SmokeTestResponse>("/smoke-test/");
  return response.data;
}

// ==========================================
// Progress Tracking & Heartbeats (FR-TRK-01 to FR-TRK-04)
// ==========================================

export async function sendHeartbeat(payload: HeartbeatPayload): Promise<HeartbeatResponse> {
  const response = await apiClient.post<HeartbeatResponse>("/progress/heartbeat/", payload);
  return response.data;
}

export async function getCourseProgress(courseSlug: string): Promise<CourseProgressDetail> {
  const response = await apiClient.get<CourseProgressDetail>(`/progress/courses/${courseSlug}/`);
  return response.data;
}

export async function markLessonComplete(lessonId: string): Promise<{
  status: string;
  lesson_id: string;
  lesson_status: string;
  course_completion_percent: number;
  is_course_completed: boolean;
}> {
  const response = await apiClient.post(`/progress/lessons/${lessonId}/complete/`);
  return response.data;
}

export async function resetCourseProgress(courseSlug: string): Promise<{
  status: string;
  message: string;
  course_completion_percent: number;
}> {
  const response = await apiClient.post(`/progress/courses/${courseSlug}/reset/`, { confirm: true });
  return response.data;
}

// ==========================================
// Adaptive Learning & Knowledge Graph (FR-PER-01 to FR-PER-05)
// ==========================================

export async function getLearningPath(courseSlug: string): Promise<LearningPath> {
  const response = await apiClient.get<LearningPath>(`/learning/paths/${courseSlug}/`);
  return response.data;
}

export async function regenerateLearningPath(courseSlug: string): Promise<LearningPath> {
  const response = await apiClient.post<LearningPath>(`/learning/paths/${courseSlug}/regenerate/`);
  return response.data;
}

export async function getStudentSkills(): Promise<Skill[]> {
  const response = await apiClient.get<Skill[]>("/learning/skills/");
  return response.data;
}

export async function evaluateSkill(
  skillSlug: string,
  score: number,
  maxScore = 100,
  asyncMode = false
): Promise<{ status: string; skill?: string; mastery_score?: number; task_id?: string }> {
  const response = await apiClient.post(`/learning/skills/${skillSlug}/evaluate/`, {
    score,
    max_score: maxScore,
    async_mode: asyncMode,
  });
  return response.data;
}

// ==========================================
// Phase 7: Assessments & Quizzes (FR-ASM-01 to FR-ASM-06)
// ==========================================

export async function getAssessment(id: string): Promise<Assessment> {
  const response = await apiClient.get<Assessment>(`/assessments/${id}/`);
  return response.data;
}

export async function getAssessmentByLesson(lessonId: string): Promise<Assessment> {
  const response = await apiClient.get<Assessment>(`/lessons/${lessonId}/assessment/`);
  return response.data;
}

export async function startQuizAttempt(assessmentId: string): Promise<QuizAttempt> {
  const response = await apiClient.post<QuizAttempt>(`/assessments/${assessmentId}/start/`);
  return response.data;
}

export async function submitQuizAttempt(
  attemptId: string,
  answers: Record<string, any>
): Promise<GradeSummary> {
  const response = await apiClient.post<GradeSummary>(`/attempts/${attemptId}/submit/`, {
    answers,
  });
  return response.data;
}

export async function getAssessmentAttempts(assessmentId: string): Promise<QuizAttempt[]> {
  const response = await apiClient.get<QuizAttempt[]>(`/assessments/${assessmentId}/attempts/`);
  return response.data;
}

// ==========================================
// Phase 7: Interactive Simulations (FR-SIM-01 to FR-SIM-03)
// ==========================================

export async function reportSimulationScore(payload: {
  block_id: string;
  score_percent: number;
  completed?: boolean;
  telemetry?: Record<string, any>;
}): Promise<{
  status: string;
  block_id: string;
  score_percent: number;
  passed: boolean;
  lesson_completed: boolean;
}> {
  const response = await apiClient.post("/content/simulations/report/", payload);
  return response.data;
}

// ==========================================
// Phase 7: Discussion Forums & Moderation (FR-DIS-01 to FR-DIS-05)
// ==========================================

export async function getCourseThreads(
  courseSlug: string,
  params?: { lesson_id?: string; search?: string }
): Promise<DiscussionThread[]> {
  const response = await apiClient.get<DiscussionThread[]>(`/courses/${courseSlug}/threads/`, {
    params,
  });
  return response.data;
}

export async function createThread(
  courseSlug: string,
  payload: { title: string; body: string; lesson_id?: string }
): Promise<DiscussionThread> {
  const response = await apiClient.post<DiscussionThread>(`/courses/${courseSlug}/threads/`, payload);
  return response.data;
}

export async function getThreadDetail(threadId: string): Promise<DiscussionThread> {
  const response = await apiClient.get<DiscussionThread>(`/threads/${threadId}/`);
  return response.data;
}

export async function addThreadReply(
  threadId: string,
  payload: { body: string; parent_id?: string }
): Promise<DiscussionPost> {
  const response = await apiClient.post<DiscussionPost>(`/threads/${threadId}/posts/`, payload);
  return response.data;
}

export async function toggleThreadVote(threadId: string): Promise<{ upvotes_count: number; has_upvoted: boolean }> {
  const response = await apiClient.post(`/threads/${threadId}/vote/`);
  return response.data;
}

export async function togglePostVote(postId: string): Promise<{ upvotes_count: number; has_upvoted: boolean }> {
  const response = await apiClient.post(`/posts/${postId}/vote/`);
  return response.data;
}

export async function endorsePost(postId: string): Promise<{ is_endorsed: boolean; endorsed_at?: string }> {
  const response = await apiClient.post(`/posts/${postId}/endorse/`);
  return response.data;
}

export async function fileContentReport(payload: {
  thread_id?: string;
  post_id?: string;
  reason: string;
  details?: string;
}): Promise<ContentReport> {
  const response = await apiClient.post<ContentReport>("/reports/", payload);
  return response.data;
}

// ==========================================
// Phase 7: Notifications (FR-NOT-01 & FR-NOT-02)
// ==========================================

export async function getNotifications(): Promise<{ unread_count: number; results: Notification[] }> {
  const response = await apiClient.get<{ unread_count: number; results: Notification[] }>("/notifications/");
  return response.data;
}

export async function markNotificationRead(id: string): Promise<{ status: string; id: string }> {
  const response = await apiClient.post(`/notifications/${id}/read/`);
  return response.data;
}

export async function markAllNotificationsRead(): Promise<{ status: string; count: number }> {
  const response = await apiClient.post("/notifications/mark-all-read/");
  return response.data;
}

// ==========================================
// Phase 8: Analytics & Telemetry (FR-ANL-01 to FR-ANL-03, FR-ADM-03)
// ==========================================

export async function getInstructorAnalytics(courseSlug: string): Promise<InstructorAnalytics> {
  const response = await apiClient.get<InstructorAnalytics>(`/analytics/instructor/${courseSlug}/`);
  return response.data;
}

export async function getAdminPlatformOverview(): Promise<AdminPlatformOverview> {
  const response = await apiClient.get<AdminPlatformOverview>("/analytics/admin/overview/");
  return response.data;
}

export async function getLearnerEngagement(): Promise<LearnerEngagementSummary> {
  const response = await apiClient.get<LearnerEngagementSummary>("/analytics/learner/engagement/");
  return response.data;
}

export async function getAuditLogs(action?: string): Promise<{ results: AuditLogEntry[] }> {
  const response = await apiClient.get<{ results: AuditLogEntry[] }>("/analytics/admin/audit-logs/", {
    params: action ? { action } : undefined,
  });
  return response.data;
}

// ==========================================
// Phase 8: GDPR Privacy & Data Subject Rights (FR-PRV-01, FR-PRV-02)
// ==========================================

export async function exportGDPRData(): Promise<any> {
  const response = await apiClient.get("/auth/privacy/export/");
  return response.data;
}

export async function requestGDPRErasure(password: string): Promise<{ status: string; message: string }> {
  const response = await apiClient.post<{ status: string; message: string }>("/auth/privacy/erase/", {
    password,
    confirm: true,
  });
  return response.data;
}


