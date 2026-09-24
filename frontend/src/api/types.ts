// 与后端 schemas.py 对齐的类型定义
export interface UserOut {
  id: number
  username: string
  name: string
  role: 'admin' | 'manager' | 'staff' | string
}

export interface TokenOut {
  access_token: string
  token_type: string
  user: UserOut
}

export interface TaskOut {
  id: number
  title: string
  description: string
  progress: string
  assignee_id: number
  creator_id: number
  priority: 'low' | 'mid' | 'high' | 'urgent' | string
  status: 'todo' | 'in_progress' | 'done' | 'blocked' | string
  due_date: string | null
  created_at: string
  completed_at: string | null
  archived: boolean
}

export interface TaskChangeLogOut {
  id: number
  task_id: number
  user_id: number
  user_name: string
  field: string
  old_value: string | null
  new_value: string | null
  created_at: string
}

export interface ParsedTask {
  title: string
  category: string | null
  duration_hours: number | null
  output: string | null
}

export interface WorkLogOut {
  id: number
  user_id: number
  log_date: string
  content: string
  parsed: { tasks?: ParsedTask[]; summary?: string } | null
  created_at: string
}

export interface ReviewContent {
  summary: string
  score_reference: string
  strengths: string[]
  risks: string[]
  suggestions: string[]
}

export interface ReviewOut {
  id: number
  user_id: number
  month: string
  content: ReviewContent
  created_at: string
}

export interface DashboardSummary {
  task_total: number
  task_done: number
  completion_rate: number
  worklog_month_count: number
  task_stats: Record<string, number>
  completion_trend: { date: string; count: number }[]
  member_load: { user_id: number; name: string; total: number; done: number }[]
  recent_tasks: TaskOut[]
}

export interface PeriodReportTask {
  title: string
  assignee: string
  status: string
  progress: string
  due_date: string | null
}

export interface PeriodReportOut {
  id: number
  kind: 'weekly' | 'midweek' | string
  period_start: string
  period_end: string
  content: {
    summary: string
    highlights: string[]
    risks: string[]
    task_count: number
    change_count: number
    tasks: PeriodReportTask[]
  }
  created_at: string
}

export interface AiConfigOut {
  base_url: string
  model: string
  api_key_set: boolean
  api_key_tail: string
  mock_mode: boolean
}
