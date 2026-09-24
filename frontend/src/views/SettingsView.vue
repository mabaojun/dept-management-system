<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAiConfig, testAiConfig, updateAiConfig } from '@/api'
import type { AiConfigOut } from '@/api/types'

const config = ref<AiConfigOut | null>(null)
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

const form = ref({ base_url: '', model: '', api_key: '' })

async function reload() {
  loading.value = true
  try {
    config.value = await getAiConfig()
    form.value = {
      base_url: config.value.base_url,
      model: config.value.model,
      api_key: '',
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.value.base_url.trim() || !form.value.model.trim()) {
    return ElMessage.warning('Base URL 和模型名称不能为空')
  }
  saving.value = true
  try {
    // api_key 留空 = 保持不变
    const body: Record<string, string> = {
      base_url: form.value.base_url.trim(),
      model: form.value.model.trim(),
    }
    if (form.value.api_key) body.api_key = form.value.api_key.trim()
    config.value = await updateAiConfig(body)
    ElMessage.success('配置已保存')
    form.value.api_key = ''
  } finally {
    saving.value = false
  }
}

async function test() {
  testing.value = true
  try {
    const r = await testAiConfig()
    ElMessage.success(`连接成功，模型回复：${r.reply}`)
  } finally {
    testing.value = false
  }
}

onMounted(reload)
</script>

<template>
  <div v-loading="loading">
    <el-card shadow="never" class="page-card" style="max-width: 720px">
      <template #header>
        <div class="card-head">
          <span>AI 接口配置</span>
          <el-tag :type="config?.mock_mode ? 'info' : 'success'" effect="plain">
            {{ config?.mock_mode ? '演示模式（未配置密钥）' : `已连接 · 密钥尾号 ****${config?.api_key_tail}` }}
          </el-tag>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
        title="兼容 OpenAI 协议的任意服务商（DeepSeek、通义千问、Kimi 等）。此处配置保存在数据库中，优先于服务器 .env 默认值。"
      />

      <el-form label-width="90px">
        <el-form-item label="API 地址">
          <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="form.model" placeholder="deepseek-chat" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="config?.api_key_set ? `已配置（尾号 ****${config.api_key_tail}），留空保持不变` : '请输入密钥'"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
          <el-button :loading="testing" :disabled="config?.mock_mode" @click="test">测试连接</el-button>
        </el-form-item>
      </el-form>

      <p class="muted">
        未配置 API Key 时，AI 解析与绩效分析返回演示数据，系统其余功能不受影响。
      </p>
    </el-card>
  </div>
</template>

<style scoped>
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
