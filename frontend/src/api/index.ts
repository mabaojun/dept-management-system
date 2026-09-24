import { http } from './http'
import type {
  AiConfigOut,
  DashboardSummary,
  PeriodReportOut,
  ReviewOut,
  TaskChangeLogOut,
  TaskOut,
  UserOut,
  WorkLogOut,
} from './types'

// ── auth ──
export const changePassword = (body: { old_password: string; new_password: string }) =>
  http.post<unknown, void>('/auth/change-password', body)

// ── users ──
export const listUsers = () => http.get<unknown, UserOut[]>('/users')
export const createUser = (body: { username: string; password: string; name: string; role: string }) =>
  http.post<unknown, UserOut>('/users', body)
export const resetUserPassword = (userId: number, newPassword: string) =>
  http.put<unknown, void>(`/users/${userId}/password`, { new_password: newPassword })
export const deleteUser = (userId: number) => http.delete<unknown, void>(`/users/${userId}`)

// ── tasks ──
export const listTasks = (params?: {
  status?: string
  assignee_id?: number
  archived?: boolean
}) => http.get<unknown, TaskOut[]>('/tasks', { params })
export const createTask = (body: {
  title: string
  description?: string
  assignee_id: number
  priority?: string
  due_date?: string | null
}) => http.post<unknown, TaskOut>('/tasks', body)
export const updateTask = (id: number, body: Record<string, unknown>) =>
  http.patch<unknown, TaskOut>(`/tasks/${id}`, body)
export const deleteTask = (id: number) => http.delete<unknown, void>(`/tasks/${id}`)
export const archiveTask = (id: number) => http.post<unknown, TaskOut>(`/tasks/${id}/archive`)
export const reopenTask = (id: number) => http.post<unknown, TaskOut>(`/tasks/${id}/reopen`)
export const getTaskChanges = (id: number) =>
  http.get<unknown, TaskChangeLogOut[]>(`/tasks/${id}/changes`)

// ── worklogs ──
export const listWorklogs = (params?: { month?: string; user_id?: number }) =>
  http.get<unknown, WorkLogOut[]>('/worklogs', { params })
export const createWorklog = (body: { log_date: string; content: string }) =>
  http.post<unknown, WorkLogOut>('/worklogs', body)
export const parseWorklog = (id: number) =>
  http.post<unknown, WorkLogOut>(`/worklogs/${id}/parse`)

// ── analysis ──
export const monthlyReview = (body: { month: string; user_id?: number }) =>
  http.post<unknown, ReviewOut>('/analysis/monthly-review', body)
export const listReviews = (params?: { user_id?: number }) =>
  http.get<unknown, ReviewOut[]>('/analysis/reviews', { params })

// ── 阶段工作总结 ──
export const listReports = () => http.get<unknown, PeriodReportOut[]>('/reports')
export const generateReport = (kind: 'weekly' | 'midweek') =>
  http.post<unknown, PeriodReportOut>('/reports/generate', { kind })

// ── dashboard ──
export const dashboardSummary = () =>
  http.get<unknown, DashboardSummary>('/dashboard/summary')

// ── 系统配置（管理员）──
export const getAiConfig = () => http.get<unknown, AiConfigOut>('/config/ai')
export const updateAiConfig = (body: { base_url?: string; model?: string; api_key?: string }) =>
  http.put<unknown, AiConfigOut>('/config/ai', body)
export const testAiConfig = () =>
  http.post<unknown, { ok: boolean; reply: string }>('/config/ai/test')
