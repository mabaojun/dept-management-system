<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { listReviews, listUsers, monthlyReview } from '@/api'
import type { ReviewOut, UserOut } from '@/api/types'

const auth = useAuthStore()

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const month = ref(currentMonth())
const targetUser = ref<number | undefined>()
const users = ref<UserOut[]>([])
const reviews = ref<ReviewOut[]>([])
const loading = ref(false)
const generating = ref(false)
const active = ref<ReviewOut | null>(null)

const userMap = ref<Record<number, string>>({})

async function reload() {
  loading.value = true
  try {
    const params = auth.isManager ? { user_id: targetUser.value } : {}
    reviews.value = await listReviews(params)
    if (reviews.value.length && !active.value) active.value = reviews.value[0]
  } finally {
    loading.value = false
  }
}

async function generate() {
  generating.value = true
  try {
    const review = await monthlyReview({
      month: month.value,
      user_id: auth.isManager ? targetUser.value : undefined,
    })
    ElMessage.success('AI 参考意见已生成')
    active.value = review
    await reload()
  } finally {
    generating.value = false
  }
}

onMounted(async () => {
  if (auth.isManager) {
    users.value = await listUsers()
    userMap.value = Object.fromEntries(users.value.map((u) => [u.id, u.name]))
  }
  await reload()
})
</script>

<template>
  <div>
    <el-alert
      type="info"
      show-icon
      :closable="false"
      class="page-card"
      title="AI 输出为绩效参考意见，不是最终考核结论；最终评分权在部门管理者。"
      description="若日志涉及不熟悉的业务流程（如某类签约流程），AI 会提示补充流程说明（步骤、文件、紧迫性），补全后可在后续版本启用自动评分。"
    />

    <div class="toolbar">
      <el-date-picker v-model="month" type="month" value-format="YYYY-MM" :clearable="false" />
      <el-select
        v-if="auth.isManager"
        v-model="targetUser"
        placeholder="选择成员（默认自己）"
        clearable
        style="width: 180px"
      >
        <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
      </el-select>
      <el-button type="primary" :loading="generating" @click="generate">生成本月 AI 参考意见</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :span="6">
        <el-card shadow="never" v-loading="loading">
          <template #header>历史意见</template>
          <el-empty v-if="!reviews.length" description="暂无记录" :image-size="60" />
          <div
            v-for="r in reviews"
            :key="r.id"
            class="review-item"
            :class="{ active: active?.id === r.id }"
            @click="active = r"
          >
            <div style="font-weight: 600">{{ r.month }} · {{ userMap[r.user_id] ?? (r.user_id === auth.user?.id ? '我' : `成员#${r.user_id}`) }}</div>
            <div class="muted">{{ new Date(r.created_at).toLocaleString('zh-CN') }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :span="18">
        <el-card shadow="never">
          <template #header>
            <span v-if="active">参考意见 · {{ active.month }}</span>
            <span v-else>参考意见</span>
          </template>
          <el-empty v-if="!active" description="生成或选择左侧记录查看" />
          <template v-else>
            <h4 style="margin: 0 0 8px">总体摘要</h4>
            <p style="margin: 0 0 16px">{{ active.content.summary }}</p>

            <h4 style="margin: 0 0 8px">评分参考</h4>
            <el-tag type="warning" size="large" effect="plain">{{ active.content.score_reference }}</el-tag>

            <h4 style="margin: 16px 0 8px">亮点</h4>
            <ul class="point-list">
              <li v-for="(s, i) in active.content.strengths" :key="i">{{ s }}</li>
            </ul>

            <h4 style="margin: 16px 0 8px">风险与关注点</h4>
            <ul class="point-list">
              <li v-for="(s, i) in active.content.risks" :key="i">{{ s }}</li>
            </ul>

            <h4 style="margin: 16px 0 8px">改进建议</h4>
            <ul class="point-list">
              <li v-for="(s, i) in active.content.suggestions" :key="i">{{ s }}</li>
            </ul>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.review-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 6px;
  border: 1px solid transparent;
}
.review-item:hover {
  background: #f5f7fa;
}
.review-item.active {
  background: #ecf5ff;
  border-color: #b3d8ff;
}
.point-list {
  margin: 0;
  padding-left: 20px;
  line-height: 1.9;
}
</style>
