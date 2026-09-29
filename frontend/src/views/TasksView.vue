<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  archiveTask,
  createTask,
  deleteTask,
  getTaskChanges,
  listTasks,
  listUsers,
  reopenTask,
  updateTask,
} from '@/api'
import type { TaskChangeLogOut, TaskOut, UserOut } from '@/api/types'

const auth = useAuthStore()

const tasks = ref<TaskOut[]>([])
const users = ref<UserOut[]>([])
const loading = ref(false)

const filterStatus = ref('')
const filterAssignee = ref<number | undefined>()
const showArchived = ref(false)

const statusLabel: Record<string, string> = {
  todo: '待开始',
  in_progress: '进行中',
  done: '已完成',
  blocked: '受阻',
}
const statusTag: Record<string, string> = {
  todo: 'info',
  in_progress: 'primary',
  done: 'success',
  blocked: 'danger',
}
const priorityLabel: Record<string, string> = { urgent: '紧急', high: '高', mid: '中', low: '低' }
const priorityTag: Record<string, string> = { urgent: 'danger', high: 'warning', mid: 'primary', low: 'info' }

// 创建/编辑对话框
const dialogVisible = ref(false)
const editing = ref<TaskOut | null>(null)
const form = ref({
  title: '',
  description: '',
  assignee_id: undefined as number | undefined,
  collaborator_ids: [] as number[],
  priority: 'mid',
  due_date: '',
})

const userMap = computed(() => Object.fromEntries(users.value.map((u) => [u.id, u.name])))

// 本人或管理侧可维护进展/详情
function canEdit(task: TaskOut) {
  return !task.archived && (auth.isManager || task.assignee_id === auth.user?.id)
}

// ── 进展叙述 / 任务详情维护 + 改动记录 ──
const fieldLabel: Record<string, string> = {
  title: '标题',
  description: '任务详情',
  progress: '进展叙述',
  assignee_id: '负责人',
  priority: '优先级',
  status: '状态',
  due_date: '截止日期',
}
const detailVisible = ref(false)
const detailTask = ref<TaskOut | null>(null)
const detailForm = ref({ status: '', description: '', progress: '' })
const detailChanges = ref<TaskChangeLogOut[]>([])
const detailLoading = ref(false)

function openDetail(task: TaskOut) {
  detailTask.value = task
  detailForm.value = { status: task.status, description: task.description, progress: task.progress }
  detailVisible.value = true
  loadChanges(task.id)
}

async function loadChanges(taskId: number) {
  detailLoading.value = true
  try {
    detailChanges.value = await getTaskChanges(taskId)
  } finally {
    detailLoading.value = false
  }
}

async function saveDetail() {
  if (!detailTask.value) return
  await updateTask(detailTask.value.id, {
    status: detailForm.value.status,
    description: detailForm.value.description,
    progress: detailForm.value.progress,
  })
  ElMessage.success('已保存，改动已记录')
  detailVisible.value = false
  reload()
}

async function reload() {
  loading.value = true
  try {
    tasks.value = await listTasks({
      status: filterStatus.value || undefined,
      assignee_id: auth.isManager ? filterAssignee.value : undefined,
      archived: showArchived.value || undefined,
    })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = {
    title: '',
    description: '',
    // 成员只能给自己建任务，负责人固定为本人
    assignee_id: auth.isManager ? undefined : auth.user?.id,
    collaborator_ids: [],
    priority: 'mid',
    due_date: '',
  }
  dialogVisible.value = true
}

function openEdit(task: TaskOut) {
  editing.value = task
  form.value = {
    title: task.title,
    description: task.description,
    assignee_id: task.assignee_id,
    collaborator_ids: [],
    priority: task.priority,
    due_date: task.due_date ?? '',
  }
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.value.title.trim()) return ElMessage.warning('请填写任务标题')
  if (!editing.value && !form.value.assignee_id) return ElMessage.warning('请选择负责人')
  const body: Record<string, unknown> = {
    title: form.value.title.trim(),
    description: form.value.description,
    collaborator_ids: form.value.collaborator_ids,
    priority: form.value.priority,
    due_date: form.value.due_date || null,
  }
  body.assignee_id = auth.isManager ? form.value.assignee_id : auth.user?.id
  if (editing.value) {
    delete body.collaborator_ids
    await updateTask(editing.value.id, body)
    ElMessage.success('任务已更新')
  } else {
    const created = await createTask(body as never)
    const n = created.length
    ElMessage.success(n > 1 ? `任务已创建，负责人与协作人共生成 ${n} 条独立任务` : '任务已创建')
  }
  dialogVisible.value = false
  reload()
}

async function changeStatus(task: TaskOut, status: string) {
  await updateTask(task.id, { status })
  task.status = status
}

async function removeTask(task: TaskOut) {
  await ElMessageBox.confirm(`确认删除任务「${task.title}」？`, '提示', { type: 'warning' })
  await deleteTask(task.id)
  ElMessage.success('已删除')
  reload()
}

async function doArchive(task: TaskOut) {
  try {
    await ElMessageBox.confirm(
      `确认将任务「${task.title}」存档？存档后不在主清单显示，可在存档区查看或重新下发。`,
      '存档任务',
      { type: 'warning', confirmButtonText: '存档', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  await archiveTask(task.id)
  ElMessage.success('任务已存档')
  reload()
}

async function doReopen(task: TaskOut) {
  try {
    await ElMessageBox.confirm(
      `确认重新下发任务「${task.title}」？任务将恢复为「待开始」并回到主清单。`,
      '重新下发',
      { type: 'info', confirmButtonText: '下发', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  await reopenTask(task.id)
  ElMessage.success('任务已重新下发')
  reload()
}

onMounted(async () => {
  // 成员名单全员加载：协作人选择与负责人列显示均需要
  users.value = await listUsers()
  await reload()
})
</script>

<template>
  <div>
    <div class="toolbar">
      <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width: 140px" @change="reload">
        <el-option v-for="(label, key) in statusLabel" :key="key" :label="label" :value="key" />
      </el-select>
      <el-select
        v-if="auth.isManager"
        v-model="filterAssignee"
        placeholder="全部成员"
        clearable
        style="width: 140px"
        @change="reload"
      >
        <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
      </el-select>
      <el-switch v-model="showArchived" active-text="显示存档" @change="reload" />
      <div style="flex: 1" />
      <el-button type="primary" :icon="Plus" @click="openCreate">新建任务</el-button>
    </div>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="tasks">
        <el-table-column prop="title" label="任务" min-width="220">
          <template #default="{ row }">
            <div style="font-weight: 600">{{ row.title }}</div>
            <div v-if="row.description" class="muted">{{ row.description }}</div>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="110">
          <template #default="{ row }">{{ userMap[row.assignee_id] ?? row.assignee_id }}</template>
        </el-table-column>
        <el-table-column label="当前进展" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.progress">{{ row.progress }}</span>
            <span v-else class="muted">暂无进展叙述</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.archived" :type="statusTag[row.status] as never" size="small">
              {{ statusLabel[row.status] }}
            </el-tag>
            <el-select v-else :model-value="row.status" size="small" @change="(v: string) => changeStatus(row, v)">
              <el-option v-for="(label, key) in statusLabel" :key="key" :label="label" :value="key" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="priorityTag[row.priority] as never" effect="plain">{{ priorityLabel[row.priority] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止" width="110" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canEdit(row)" link type="primary" @click="openDetail(row)">进展</el-button>
            <el-button v-if="row.archived && auth.isManager" link type="warning" @click="doReopen(row)">重新下发</el-button>
            <el-button v-else-if="row.status === 'done' && auth.isManager" link type="primary" @click="doArchive(row)">存档</el-button>
            <el-button v-if="auth.isManager && !row.archived" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="auth.isManager" link type="danger" @click="removeTask(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 进展/详情维护 + 改动记录 -->
    <el-dialog v-model="detailVisible" :title="detailTask ? `任务进展 · ${detailTask.title}` : '任务进展'" width="640px">
      <el-form label-width="80px">
        <el-form-item label="状态">
          <el-radio-group v-model="detailForm.status">
            <el-radio-button v-for="(label, key) in statusLabel" :key="key" :value="key">{{ label }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="当前进展">
          <el-input
            v-model="detailForm.progress"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="描述当前推进情况，例如：初稿已完成，等待客户反馈后修订。"
          />
        </el-form-item>
        <el-form-item label="任务详情">
          <el-input
            v-model="detailForm.description"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="任务背景、要求、产出物等详细内容。"
          />
        </el-form-item>
      </el-form>

      <el-divider content-position="left">改动记录</el-divider>
      <div v-loading="detailLoading" style="min-height: 60px; max-height: 260px; overflow: auto">
        <el-empty v-if="!detailLoading && !detailChanges.length" description="暂无改动记录" :image-size="60" />
        <el-timeline v-else style="padding-left: 4px">
          <el-timeline-item
            v-for="c in detailChanges"
            :key="c.id"
            :timestamp="`${c.user_name} · ${new Date(c.created_at).toLocaleString('zh-CN')}`"
            placement="top"
            type="primary"
          >
            <b>{{ fieldLabel[c.field] ?? c.field }}</b>
            <template v-if="c.field === 'status' || c.field === 'priority'">
              ：{{ c.old_value || '空' }} → {{ c.new_value || '空' }}
            </template>
            <template v-else>
              <div class="muted" style="font-size: 12px; white-space: pre-wrap">
                {{ c.old_value ? `旧：${c.old_value.slice(0, 80)}` : '旧：空' }}
              </div>
              <div style="font-size: 12px; white-space: pre-wrap">
                {{ c.new_value ? `新：${c.new_value.slice(0, 120)}` : '新：空' }}
              </div>
            </template>
          </el-timeline-item>
        </el-timeline>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDetail">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑任务' : '新建任务'" width="520px">
      <el-form label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-if="auth.isManager"
            v-model="form.assignee_id"
            placeholder="选择成员"
            style="width: 100%"
          >
            <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
          <el-input v-else :model-value="auth.user?.name" disabled />
        </el-form-item>
        <el-form-item label="协作人">
          <el-select
            v-model="form.collaborator_ids"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="可选，选择协作成员"
            style="width: 100%"
          >
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="u.name"
              :value="u.id"
              :disabled="u.id === form.assignee_id"
            />
          </el-select>
          <div class="muted" style="font-size: 12px; line-height: 1.5; margin-top: 4px">
            保存后将按负责人和每位协作人各生成一条内容相同的独立任务，各自单独跟进进展。
          </div>
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio-button v-for="(label, key) in priorityLabel" :key="key" :value="key">{{ label }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
