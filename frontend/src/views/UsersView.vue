<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Key, Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { createUser, deleteUser, listUsers, resetUserPassword } from '@/api'
import type { UserOut } from '@/api/types'

const auth = useAuthStore()

const users = ref<UserOut[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const form = ref({ username: '', password: '', name: '', role: 'staff' })

// 重置密码
const resetVisible = ref(false)
const resetTarget = ref<UserOut | null>(null)
const resetPwd = ref('')
const resetLoading = ref(false)

const roleLabel: Record<string, string> = {
  admin: '系统管理员',
  manager: '部门管理者',
  staff: '部门成员',
}
const roleTag: Record<string, string> = { admin: 'danger', manager: 'warning', staff: 'info' }

async function reload() {
  loading.value = true
  try {
    users.value = await listUsers()
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  if (!form.value.username.trim() || !form.value.password || !form.value.name.trim()) {
    return ElMessage.warning('请完整填写用户名、密码、姓名')
  }
  await createUser({ ...form.value, username: form.value.username.trim() })
  ElMessage.success('成员已创建')
  dialogVisible.value = false
  form.value = { username: '', password: '', name: '', role: 'staff' }
  reload()
}

function openReset(user: UserOut) {
  resetTarget.value = user
  resetPwd.value = ''
  resetVisible.value = true
}

async function submitReset() {
  if (!resetTarget.value) return
  if (resetPwd.value.length < 6) return ElMessage.warning('新密码至少 6 位')
  resetLoading.value = true
  try {
    await resetUserPassword(resetTarget.value.id, resetPwd.value)
    ElMessage.success(`已重置「${resetTarget.value.name}」的密码`)
    resetVisible.value = false
  } finally {
    resetLoading.value = false
  }
}

async function handleDelete(user: UserOut) {
  try {
    await ElMessageBox.confirm(
      `确定删除成员「${user.name}」吗？删除后不可恢复；若其名下存在任务/日志/绩效记录，需先处理后再删除。`,
      '删除成员',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await deleteUser(user.id)
    ElMessage.success('成员已删除')
    reload()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  }
}

onMounted(reload)
</script>

<template>
  <div>
    <div class="toolbar">
      <div style="flex: 1" />
      <el-button type="primary" :icon="Plus" @click="dialogVisible = true">新增成员</el-button>
    </div>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="users">
        <el-table-column prop="username" label="用户名" width="160" />
        <el-table-column prop="name" label="姓名" width="160" />
        <el-table-column label="角色" width="140">
          <template #default="{ row }">
            <el-tag :type="roleTag[row.role]" effect="plain">
              {{ roleLabel[row.role] ?? row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              v-if="auth.user?.role === 'admin'"
              link
              type="primary"
              :icon="Key"
              @click="openReset(row)"
            >
              重置密码
            </el-button>
            <el-button
              v-if="auth.user?.role === 'admin' && row.id !== auth.user?.id"
              link
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增成员" width="460px">
      <el-form label-width="70px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" maxlength="30" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" maxlength="30" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="form.password" type="password" show-password maxlength="64" placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="部门成员" value="staff" />
            <el-option label="部门管理者" value="manager" />
            <el-option label="系统管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetVisible" :title="`重置密码 · ${resetTarget?.name ?? ''}`" width="400px">
      <el-form label-width="70px">
        <el-form-item label="新密码">
          <el-input
            v-model="resetPwd"
            type="password"
            show-password
            maxlength="64"
            placeholder="至少 6 位"
            @keyup.enter="submitReset"
          />
        </el-form-item>
      </el-form>
      <p class="muted" style="margin: 0 0 8px">重置后请告知该成员使用新密码重新登录。</p>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetLoading" @click="submitReset">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
