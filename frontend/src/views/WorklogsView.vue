<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  createWorklog,
  generateReport,
  listReports,
  listUsers,
  listWorklogs,
  parseWorklog,
} from '@/api'
import type { PeriodReportOut, UserOut, WorkLogOut } from '@/api/types'

const auth = useAuthStore()

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const activeTab = ref('logs')

// ── 工作日志 ──
const logs = ref<WorkLogOut[]>([])
const users = ref<UserOut[]>([])
const month = ref(currentMonth())
const filterUser = ref<number | undefined>()
const loading = ref(false)
const parsingId = ref<number | null>(null)

const dialogVisible = ref(false)
const form = ref({ log_date: new Date().toISOString().slice(0, 10), content: '' })

const userMap = computed(() => Object.fromEntries(users.value.map((u) => [u.id, u.name])))

const statusLabel: Record<string, string> = {
  todo: '待开始',
  in_progress: '进行中',
  done: '已完成',
  blocked: '受阻',
}

async function reload() {
  loading.value = true
  try {
    logs.value = await listWorklogs({
      month: month.value || undefined,
      user_id: auth.isManager ? filterUser.value : undefined,
    })
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  if (!form.value.content.trim()) return ElMessage.warning('请填写日志内容')
  await createWorklog({ log_date: form.value.log_date, content: form.value.content.trim() })
  ElMessage.success('日志已上报')
  dialogVisible.value = false
  reload()
}

async function runParse(log: WorkLogOut) {
  parsingId.value = log.id
  try {
    const updated = await parseWorklog(log.id)
    Object.assign(log, updated)
    ElMessage.success('AI 解析完成')
  } finally {
    parsingId.value = null
  }
}

// ── 阶段工作总结 ──
const reports = ref<PeriodReportOut[]>([])
const reportsLoading = ref(false)
const generating = ref('')

const kindLabel: Record<string, string> = { weekly: '周五周报', midweek: '周二简报' }
const kindTag: Record<string, string> = { weekly: 'success', midweek: 'warning' }

async function loadReports() {
  reportsLoading.value = true
  try {
    reports.value = await listReports()
  } finally {
    reportsLoading.value = false
  }
}

async function doGenerate(kind: 'weekly' | 'midweek') {
  generating.value = kind
  try {
    await generateReport(kind)
    ElMessage.success('阶段总结已生成')
    await loadReports()
  } finally {
    generating.value = ''
  }
}

function switchTab(tab: string | number) {
  if (tab === 'reports' && !reports.value.length) loadReports()
}

onMounted(async () => {
  if (auth.isManager) users.value = await listUsers()
  await reload()
  loadReports()
})
</script>

<template>
  <div>
    <el-tabs v-model="activeTab" @tab-change="switchTab">
      <el-tab-pane label="工作日志" name="logs">
        <div class="toolbar">
          <el-date-picker v-model="month" type="month" value-format="YYYY-MM" placeholder="选择月份" :clearable="false" @change="reload" />
          <el-select
            v-if="auth.isManager"
            v-model="filterUser"
            placeholder="全部成员"
            clearable
            style="width: 140px"
            @change="reload"
          >
            <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
          <div style="flex: 1" />
          <el-button type="primary" :icon="Plus" @click="dialogVisible = true">上报日志</el-button>
        </div>

        <el-card shadow="never">
          <el-table v-loading="loading" :data="logs" row-key="id">
            <el-table-column type="expand">
              <template #default="{ row }">
                <div style="padding: 8px 24px 16px">
                  <template v-if="row.parsed?.tasks?.length">
                    <p style="margin: 0 0 8px; font-weight: 600">AI 解析结果</p>
                    <p v-if="row.parsed?.summary" class="muted" style="margin: 0 0 8px">{{ row.parsed.summary }}</p>
                    <el-table :data="row.parsed.tasks" size="small" border>
                      <el-table-column prop="title" label="工作事项" min-width="180" />
                      <el-table-column prop="category" label="类别" width="110">
                        <template #default="{ row: t }">{{ t.category ?? '—' }}</template>
                      </el-table-column>
                      <el-table-column prop="duration_hours" label="时长(h)" width="90">
                        <template #default="{ row: t }">{{ t.duration_hours ?? '—' }}</template>
                      </el-table-column>
                      <el-table-column prop="output" label="产出" min-width="160">
                        <template #default="{ row: t }">{{ t.output ?? '—' }}</template>
                      </el-table-column>
                    </el-table>
                  </template>
                  <template v-else>
                    <p class="muted" style="margin: 0">尚未解析，点击「AI 解析」自动提取工作事项、类别、时长与产出。</p>
                  </template>
                </div>
              </template>
            </el-table-column>
            <el-table-column v-if="auth.isManager" label="成员" width="100">
              <template #default="{ row }">{{ userMap[row.user_id] ?? row.user_id }}</template>
            </el-table-column>
            <el-table-column prop="log_date" label="日期" width="110" />
            <el-table-column prop="content" label="日志内容" min-width="300" show-overflow-tooltip />
            <el-table-column label="解析状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.parsed ? 'success' : 'info'" size="small">
                  {{ row.parsed ? '已解析' : '未解析' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  :icon="MagicStick"
                  :loading="parsingId === row.id"
                  @click="runParse(row)"
                >
                  AI 解析
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="阶段总结" name="reports">
        <div class="toolbar">
          <span class="muted">每周二 / 周五 17:00 系统自动结合改动日志生成当前周期任务进展。</span>
          <div style="flex: 1" />
          <el-button
            v-if="auth.isManager"
            :loading="generating === 'midweek'"
            @click="doGenerate('midweek')"
          >
            生成当前简报
          </el-button>
          <el-button
            v-if="auth.isManager"
            type="primary"
            :loading="generating === 'weekly'"
            @click="doGenerate('weekly')"
          >
            生成当前周报
          </el-button>
        </div>

        <div v-loading="reportsLoading">
          <el-empty v-if="!reportsLoading && !reports.length" description="暂无阶段总结，等待定时生成或手动触发" />
          <el-card v-for="r in reports" :key="r.id" shadow="never" class="report-card">
            <div class="report-head">
              <el-tag :type="(kindTag[r.kind] ?? 'info') as never">{{ kindLabel[r.kind] ?? r.kind }}</el-tag>
              <span class="report-period">{{ r.period_start }} ~ {{ r.period_end }}</span>
              <span class="muted">
                任务 {{ r.content.task_count }} 项 · 改动 {{ r.content.change_count }} 条 ·
                生成于 {{ new Date(r.created_at).toLocaleString('zh-CN') }}
              </span>
            </div>
            <p class="report-summary">{{ r.content.summary }}</p>
            <el-row v-if="r.content.highlights?.length || r.content.risks?.length" :gutter="16">
              <el-col v-if="r.content.highlights?.length" :xs="24" :span="12">
                <p class="block-title success">亮点</p>
                <ul class="block-list">
                  <li v-for="(h, i) in r.content.highlights" :key="i">{{ h }}</li>
                </ul>
              </el-col>
              <el-col v-if="r.content.risks?.length" :xs="24" :span="12">
                <p class="block-title danger">风险与关注</p>
                <ul class="block-list">
                  <li v-for="(k, i) in r.content.risks" :key="i">{{ k }}</li>
                </ul>
              </el-col>
            </el-row>
            <el-collapse>
              <el-collapse-item :title="`任务进展明细（${r.content.tasks?.length ?? 0} 项）`">
                <el-table :data="r.content.tasks" size="small" border>
                  <el-table-column prop="title" label="任务" min-width="200" show-overflow-tooltip />
                  <el-table-column prop="assignee" label="负责人" width="90" />
                  <el-table-column label="状态" width="90">
                    <template #default="{ row }">{{ statusLabel[row.status] ?? row.status }}</template>
                  </el-table-column>
                  <el-table-column prop="progress" label="当前进展" min-width="200" show-overflow-tooltip>
                    <template #default="{ row }">{{ row.progress || '—' }}</template>
                  </el-table-column>
                  <el-table-column prop="due_date" label="截止" width="110">
                    <template #default="{ row }">{{ row.due_date ?? '—' }}</template>
                  </el-table-column>
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dialogVisible" title="上报工作日志" width="560px">
      <el-form label-width="60px">
        <el-form-item label="日期">
          <el-date-picker v-model="form.log_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="用自然语言描述今天/近期完成的工作，例如：上午完成 A 项目合同初稿（约 3 小时），下午陪同客户走完签约流程并整理会议纪要。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.report-card {
  margin-bottom: 14px;
  border-radius: 10px;
}
.report-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.report-period {
  font-weight: 600;
}
.report-summary {
  margin: 6px 0 12px;
  line-height: 1.7;
}
.block-title {
  margin: 0 0 6px;
  font-weight: 600;
}
.block-title.success {
  color: #67c23a;
}
.block-title.danger {
  color: #f56c6c;
}
.block-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
}
</style>
