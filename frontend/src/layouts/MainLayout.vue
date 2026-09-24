<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Document, Odometer, Setting, Tickets, User, Monitor, Menu as MenuIcon } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { changePassword } from '@/api'
import { useIsMobile } from '@/composables/useIsMobile'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { isMobile } = useIsMobile()

// 手机端侧边栏抽屉
const drawerVisible = ref(false)

const menuItems = [
  { index: '/dashboard', title: '数据看板', icon: Odometer },
  { index: '/tasks', title: '任务管理', icon: Tickets },
  { index: '/worklogs', title: '工作日志', icon: Document },
  { index: '/analysis', title: 'AI 绩效分析', icon: DataAnalysis },
  { index: '/users', title: '成员管理', icon: User, managerOnly: true },
  { index: '/settings', title: '系统设置', icon: Setting, adminOnly: true },
]

const visibleItems = menuItems.filter(
  (i) =>
    (!i.managerOnly || auth.isManager) &&
    (!i.adminOnly || auth.user?.role === 'admin'),
)

const roleLabel: Record<string, string> = {
  admin: '系统管理员',
  manager: '部门管理者',
  staff: '部门成员',
}

// ── 修改密码 ──
const pwdVisible = ref(false)
const pwdForm = ref({ old_password: '', new_password: '', confirm: '' })
const pwdLoading = ref(false)

function openPwdDialog() {
  pwdForm.value = { old_password: '', new_password: '', confirm: '' }
  pwdVisible.value = true
}

async function submitPwd() {
  const f = pwdForm.value
  if (!f.old_password || !f.new_password) return ElMessage.warning('请填写完整')
  if (f.new_password.length < 6) return ElMessage.warning('新密码至少 6 位')
  if (f.new_password !== f.confirm) return ElMessage.warning('两次输入的新密码不一致')
  pwdLoading.value = true
  try {
    await changePassword({ old_password: f.old_password, new_password: f.new_password })
    ElMessage.success('密码修改成功')
    pwdVisible.value = false
  } finally {
    pwdLoading.value = false
  }
}

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  } else if (cmd === 'password') {
    openPwdDialog()
  }
}

function onMenuSelect() {
  if (isMobile.value) drawerVisible.value = false
}
</script>

<template>
  <el-container style="height: 100vh">
    <!-- 桌面端固定侧边栏 -->
    <el-aside v-if="!isMobile" width="220px" style="background: #001529">
      <div class="logo">
        <el-icon :size="20" color="#7ed957"><Monitor /></el-icon>
        <span>青青草原牛马管理系统</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#ffffff"
        style="border-right: none"
        @select="onMenuSelect"
      >
        <el-menu-item v-for="item in visibleItems" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 手机端抽屉侧边栏 -->
    <el-drawer v-if="isMobile" v-model="drawerVisible" direction="ltr" size="220px" :with-header="false">
      <div style="background: #001529; height: 100%">
        <div class="logo">
          <el-icon :size="20" color="#7ed957"><Monitor /></el-icon>
          <span style="font-size: 14px">青青草原牛马管理系统</span>
        </div>
        <el-menu
          :default-active="route.path"
          router
          background-color="#001529"
          text-color="#a6adb4"
          active-text-color="#ffffff"
          style="border-right: none"
          @select="onMenuSelect"
        >
          <el-menu-item v-for="item in visibleItems" :key="item.index" :index="item.index">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-drawer>

    <el-container>
      <el-header height="56px" class="header">
        <div class="header-left">
          <el-icon v-if="isMobile" class="burger" :size="20" @click="drawerVisible = true">
            <MenuIcon />
          </el-icon>
          <span class="page-title" style="margin: 0">{{ route.meta.title }}</span>
        </div>
        <el-dropdown @command="onCommand">
          <span class="user-chip">
            {{ auth.user?.name }}
            <el-tag v-if="!isMobile" size="small" type="info">{{ roleLabel[auth.user?.role ?? ''] }}</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main :style="isMobile ? 'padding: 12px' : 'padding: 16px 20px'">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="pwdVisible" title="修改密码" width="420px">
      <el-form label-width="80px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdForm.confirm" type="password" show-password @keyup.enter="submitPwd" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitPwd">确定</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<style scoped>
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 56px;
  padding: 0 20px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.burger {
  cursor: pointer;
  color: #303133;
  flex-shrink: 0;
}
.page-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}
</style>
