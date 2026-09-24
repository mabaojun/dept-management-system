<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ username: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <!-- 太阳 -->
    <div class="sun">
      <div class="sun-core" />
    </div>
    <!-- 云朵 -->
    <div class="cloud cloud-1" />
    <div class="cloud cloud-2" />
    <div class="cloud cloud-3" />

    <!-- 青青草原 -->
    <svg class="hills" viewBox="0 0 1440 320" preserveAspectRatio="none" aria-hidden="true">
      <path fill="#8ed16f" d="M0 220 C 240 120 420 260 720 190 C 1000 125 1200 240 1440 170 L 1440 320 L 0 320 Z" />
      <path fill="#6cbf4b" d="M0 270 C 300 200 600 300 900 240 C 1150 195 1300 280 1440 240 L 1440 320 L 0 320 Z" />
      <path fill="#57ad3a" d="M0 320 C 400 270 900 330 1440 290 L 1440 320 Z" />
    </svg>

    <el-card class="login-card" shadow="always">
      <div class="login-head">
        <svg class="sheep" viewBox="0 0 120 100" aria-hidden="true">
          <!-- 羊身 -->
          <g fill="#ffffff" stroke="#2c3e50" stroke-width="3">
            <circle cx="34" cy="58" r="20" />
            <circle cx="52" cy="44" r="22" />
            <circle cx="74" cy="52" r="20" />
            <circle cx="58" cy="66" r="21" />
            <circle cx="44" cy="68" r="18" />
            <circle cx="68" cy="68" r="18" />
          </g>
          <!-- 脸 -->
          <ellipse cx="88" cy="52" rx="16" ry="13" fill="#3d3d3d" />
          <!-- 羊角 -->
          <path d="M84 40 C 80 28 90 24 94 32 C 96 27 104 28 101 36" fill="none" stroke="#e8b96f" stroke-width="5" stroke-linecap="round" />
          <!-- 眼睛 -->
          <circle cx="92" cy="49" r="2.6" fill="#fff" />
          <circle cx="99" cy="49" r="2.6" fill="#fff" />
          <!-- 腿 -->
          <rect x="42" y="82" width="6" height="12" rx="3" fill="#3d3d3d" />
          <rect x="68" y="82" width="6" height="12" rx="3" fill="#3d3d3d" />
        </svg>
        <h2>青青草原牛马管理系统</h2>
        <p class="slogan">任务 · 日志 · AI 绩效分析 —— 好好干活，天天向上</p>
      </div>
      <el-form @submit.prevent="submit">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" autofocus />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button class="go-btn" size="large" :loading="loading" native-type="submit">
          出发打工！
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #6ec6f5 0%, #9adcfa 55%, #c9f0ff 100%);
}

/* 太阳 */
.sun {
  position: absolute;
  top: 48px;
  right: 90px;
  width: 120px;
  height: 120px;
}
.sun-core {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(circle at 38% 35%, #fff6c9 0%, #ffd94d 45%, #ffc233 100%);
  box-shadow:
    0 0 0 18px rgba(255, 226, 120, 0.35),
    0 0 0 38px rgba(255, 226, 120, 0.18),
    0 0 60px rgba(255, 200, 60, 0.6);
  animation: sun-pulse 4s ease-in-out infinite;
}
@keyframes sun-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 云朵 */
.cloud {
  position: absolute;
  background: #fff;
  border-radius: 999px;
  opacity: 0.92;
}
.cloud::before,
.cloud::after {
  content: '';
  position: absolute;
  background: #fff;
  border-radius: 50%;
}
.cloud-1 {
  top: 90px; left: 8%;
  width: 130px; height: 44px;
  animation: drift 26s linear infinite;
}
.cloud-1::before { width: 60px; height: 60px; top: -30px; left: 22px; }
.cloud-1::after { width: 44px; height: 44px; top: -20px; left: 66px; }
.cloud-2 {
  top: 200px; left: 24%;
  width: 90px; height: 32px;
  opacity: 0.75;
  animation: drift 34s linear infinite reverse;
}
.cloud-2::before { width: 42px; height: 42px; top: -21px; left: 16px; }
.cloud-2::after { width: 30px; height: 30px; top: -14px; left: 46px; }
.cloud-3 {
  top: 60px; left: 55%;
  width: 160px; height: 50px;
  opacity: 0.85;
  animation: drift 40s linear infinite;
}
.cloud-3::before { width: 70px; height: 70px; top: -34px; left: 28px; }
.cloud-3::after { width: 52px; height: 52px; top: -24px; left: 82px; }
@keyframes drift {
  from { transform: translateX(-16vw); }
  to { transform: translateX(110vw); }
}

/* 草原 */
.hills {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 34vh;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  padding: 10px 14px 18px;
  border-radius: 22px;
  border: 3px solid #2f6f2f;
  box-shadow: 0 18px 40px rgba(20, 80, 20, 0.28);
}
.login-head {
  text-align: center;
  margin-bottom: 18px;
}
.sheep {
  width: 104px;
  height: 88px;
  animation: hop 2.6s ease-in-out infinite;
}
@keyframes hop {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-7px); }
}
.login-head h2 {
  margin: 4px 0 6px;
  font-size: 24px;
  font-weight: 800;
  color: #2f6f2f;
  letter-spacing: 1px;
}
.slogan {
  margin: 0;
  font-size: 13px;
  color: #7a8b7a;
}

.go-btn {
  width: 100%;
  height: 46px;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  border: none;
  border-radius: 999px;
  background: linear-gradient(180deg, #7ed957 0%, #4caf3f 100%);
  box-shadow: 0 6px 0 #3c8c31;
  transition: transform 0.12s ease;
}
.go-btn:hover {
  transform: translateY(-2px);
  color: #fff;
  background: linear-gradient(180deg, #8fe468 0%, #55ba46 100%);
}
.go-btn:active {
  transform: translateY(3px);
  box-shadow: 0 2px 0 #3c8c31;
}
</style>
