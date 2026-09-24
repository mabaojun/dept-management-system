<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import { dashboardSummary } from '@/api'
import type { DashboardSummary } from '@/api/types'
import { useIsMobile } from '@/composables/useIsMobile'

const { isMobile } = useIsMobile()
const chartHeight = computed(() => (isMobile.value ? '220px' : '260px'))

const summary = ref<DashboardSummary | null>(null)

const statusLabel: Record<string, string> = {
  todo: '待开始',
  in_progress: '进行中',
  done: '已完成',
  blocked: '受阻',
}
const statusColor: Record<string, string> = {
  todo: '#909399',
  in_progress: '#409eff',
  done: '#67c23a',
  blocked: '#f56c6c',
}
const priorityLabel: Record<string, string> = { urgent: '紧急', high: '高', mid: '中', low: '低' }
const priorityTag: Record<string, string> = { urgent: 'danger', high: 'warning', mid: 'info', low: 'info' }

const pieEl = ref<HTMLElement>()
const trendEl = ref<HTMLElement>()
const loadEl = ref<HTMLElement>()
let charts: echarts.ECharts[] = []

function renderCharts(s: DashboardSummary) {
  charts.forEach((c) => c.dispose())
  charts = []
  if (pieEl.value) {
    const pie = echarts.init(pieEl.value)
    pie.setOption({
      tooltip: { trigger: 'item' },
      // 底部滚动图例：窄容器下不再截断
      legend: {
        bottom: 0,
        type: 'scroll',
        itemWidth: 12,
        itemHeight: 8,
        itemGap: 8,
        textStyle: { fontSize: 11 },
      },
      series: [
        {
          type: 'pie',
          radius: ['38%', '58%'],
          center: ['50%', '42%'],
          avoidLabelOverlap: true,
          label: { formatter: '{b}: {c}', fontSize: 11 },
          labelLine: { length: 8, length2: 6 },
          data: Object.entries(s.task_stats).map(([k, v]) => ({
            name: statusLabel[k] ?? k,
            value: v,
            itemStyle: { color: statusColor[k] },
          })),
        },
      ],
    })
    charts.push(pie)
  }
  if (trendEl.value) {
    const trend = echarts.init(trendEl.value)
    trend.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: s.completion_trend.map((d) => d.date.slice(5)) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          type: 'line',
          smooth: true,
          areaStyle: { opacity: 0.15 },
          data: s.completion_trend.map((d) => d.count),
          itemStyle: { color: '#409eff' },
        },
      ],
    })
    charts.push(trend)
  }
  if (loadEl.value) {
    const load = echarts.init(loadEl.value)
    const names = s.member_load.map((m) => m.name)
    load.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['已完成', '未完成'], right: 0, itemWidth: 12, itemHeight: 8, textStyle: { fontSize: 11 } },
      grid: { left: 60, right: 16, top: 30 },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: { type: 'category', data: names, inverse: true, axisLabel: { fontSize: 11 } },
      series: [
        { name: '已完成', type: 'bar', stack: 'x', itemStyle: { color: '#67c23a' }, data: s.member_load.map((m) => m.done) },
        { name: '未完成', type: 'bar', stack: 'x', itemStyle: { color: '#909399' }, data: s.member_load.map((m) => m.total - m.done) },
      ],
    })
    charts.push(load)
  }
}

function onResize() {
  charts.forEach((c) => c.resize())
}

onMounted(async () => {
  summary.value = await dashboardSummary()
  // 等待 v-if 区块随 DOM 更新挂载完成，否则负载图容器 ref 尚不存在，图表不会初始化
  await nextTick()
  renderCharts(summary.value)
  window.addEventListener('resize', onResize)
})
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<template>
  <div>
    <el-row :gutter="16" class="page-card">
      <el-col :xs="12" :span="6">
        <el-card shadow="never"><el-statistic title="任务总数" :value="summary?.task_total ?? 0" /></el-card>
      </el-col>
      <el-col :xs="12" :span="6">
        <el-card shadow="never"><el-statistic title="已完成" :value="summary?.task_done ?? 0" /></el-card>
      </el-col>
      <el-col :xs="12" :span="6">
        <el-card shadow="never">
          <el-statistic title="完成率" :value="((summary?.completion_rate ?? 0) * 100).toFixed(1)" suffix="%" />
        </el-card>
      </el-col>
      <el-col :xs="12" :span="6">
        <el-card shadow="never"><el-statistic title="本月日志数" :value="summary?.worklog_month_count ?? 0" /></el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="page-card">
      <el-col :xs="24" :span="8">
        <el-card shadow="never">
          <template #header>任务状态分布</template>
          <div ref="pieEl" :style="{ height: chartHeight }" />
        </el-card>
      </el-col>
      <el-col :xs="24" :span="16">
        <el-card shadow="never">
          <template #header>近 14 天完成任务趋势</template>
          <div ref="trendEl" :style="{ height: chartHeight }" />
        </el-card>
      </el-col>
    </el-row>

    <el-row v-if="summary?.member_load?.length" :gutter="16" class="page-card">
      <el-col :xs="24" :span="24">
        <el-card shadow="never">
          <template #header>成员任务负载</template>
          <div ref="loadEl" :style="{ height: isMobile ? '300px' : '240px' }" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>最近更新的未完成任务</template>
      <el-table :data="summary?.recent_tasks ?? []" size="large">
        <el-table-column prop="title" label="任务" min-width="220" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :color="statusColor[row.status]" effect="dark" style="border: none">
              {{ statusLabel[row.status] ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="priorityTag[row.priority]" effect="plain">
              {{ priorityLabel[row.priority] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止日期" width="120" />
      </el-table>
    </el-card>
  </div>
</template>
