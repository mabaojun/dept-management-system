import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: '数据看板' } },
        { path: 'tasks', name: 'tasks', component: () => import('@/views/TasksView.vue'), meta: { title: '任务管理' } },
        { path: 'worklogs', name: 'worklogs', component: () => import('@/views/WorklogsView.vue'), meta: { title: '工作日志' } },
        { path: 'analysis', name: 'analysis', component: () => import('@/views/AnalysisView.vue'), meta: { title: 'AI 绩效分析' } },
        { path: 'users', name: 'users', component: () => import('@/views/UsersView.vue'), meta: { title: '成员管理', managerOnly: true } },
        { path: 'settings', name: 'settings', component: () => import('@/views/SettingsView.vue'), meta: { title: '系统设置', adminOnly: true } },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.token) return '/login'
  if (to.meta.managerOnly && !auth.isManager) return '/dashboard'
  if (to.meta.adminOnly && auth.user?.role !== 'admin') return '/dashboard'
  return true
})

export default router
