<template>
  <app-layout current-page-key="dashboard">
    <a-card title="仪表盘">


      <!-- 工具调用统计 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="6">
          <a-card>
            <template #title>
              <ApiOutlined /> 总调用
            </template>
            <div class="stat-card">
              <div class="stat-number">{{ toolStats.total_calls }}</div>
              <div class="stat-label">工具调用次数</div>
            </div>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card>
            <template #title>
              <CheckCircleOutlined /> 成功率
            </template>
            <div class="stat-card">
              <div class="stat-number success">{{ toolStats.success_rate }}%</div>
              <div class="stat-label">调用成功率</div>
            </div>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card>
            <template #title>
              <ClockCircleOutlined /> 平均耗时
            </template>
            <div class="stat-card">
              <div class="stat-number">{{ formatDuration(toolStats.avg_duration_ms) }}</div>
              <div class="stat-label">平均响应时间</div>
            </div>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card>
            <template #title>
              <CalendarOutlined /> 今日调用
            </template>
            <div class="stat-card">
              <div class="stat-number">{{ toolStats.calls_today }}</div>
              <div class="stat-label">今日调用次数</div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 工具调用趋势图表 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="24">
          <a-card title="工具调用趋势">
            <div ref="chartContainer" style="height: 300px;"></div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 最近调用日志 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="24">
          <a-card title="最近调用日志">
            <template #extra>
              <a-button type="link" @click="router.push('/tool-log')">查看更多</a-button>
            </template>

            <a-table
              :columns="logColumns"
              :data-source="recentLogs"
              :loading="logsLoading"
              :pagination="false"
              size="small"
              row-key="id"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'tool_name'">
                  <a-tag color="blue">{{ record.tool_name }}</a-tag>
                </template>
                <template v-else-if="column.key === 'call_type'">
                  <a-tag :color="record.call_type === 'mcp' ? 'purple' : 'orange'">
                    {{ record.call_type === 'mcp' ? 'MCP' : '调试' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'is_success'">
                  <a-tag :color="record.is_success ? 'green' : 'red'">
                    {{ record.is_success ? '成功' : '失败' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'duration_ms'">
                  <span v-if="record.duration_ms">
                    {{ formatDuration(record.duration_ms) }}
                  </span>
                  <span v-else>-</span>
                </template>
                <template v-else-if="column.key === 'request_time'">
                  {{ formatTimestamp(record.request_time) }}
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  ApiOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CalendarOutlined
} from '@ant-design/icons-vue'
import { callApi } from '../utils/api-util'
import { formatTimestamp } from '../utils/api-util'
import AppLayout from '../components/AppLayout.vue'
import * as echarts from 'echarts'

const router = useRouter()
const loading = ref(false)
const chartContainer = ref(null)
let chart = null

const toolStats = reactive({
  total_calls: 0,
  success_calls: 0,
  failed_calls: 0,
  success_rate: 0,
  avg_duration_ms: 0,
  calls_today: 0,
  calls_this_week: 0,
  calls_this_month: 0,
  mcp_calls: 0,
  debug_calls: 0
})

const toolTrends = ref([])
const recentLogs = ref([])
const logsLoading = ref(false)

// 日志表格列定义
const logColumns = [
  {
    title: '工具名称',
    dataIndex: 'tool_name',
    key: 'tool_name',
    width: 120
  },
  {
    title: '类型',
    dataIndex: 'call_type',
    key: 'call_type',
    width: 80
  },
  {
    title: '状态',
    dataIndex: 'is_success',
    key: 'is_success',
    width: 80
  },
  {
    title: '耗时',
    dataIndex: 'duration_ms',
    key: 'duration_ms',
    width: 80
  },
  {
    title: '请求时间',
    dataIndex: 'request_time',
    key: 'request_time',
    width: 160
  }
]

onMounted(async () => {
  loading.value = true

  try {
    // Fetch tool stats
    await fetchToolStats()

    // Fetch tool trends
    await fetchToolTrends()

    // Fetch recent logs
    await fetchRecentLogs()

    // Initialize chart after data is loaded
    await nextTick()
    initChart()
  } finally {
    loading.value = false
  }
})

const fetchToolStats = async () => {
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tool-log/stats',
      onSuccess: (data) => {
        Object.assign(toolStats, data)
      }
    })
  } catch (error) {
    console.error('Error fetching tool stats:', error)
  }
}

const fetchToolTrends = async () => {
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tool-log/trends',
      params: { days: 7 },
      onSuccess: (data) => {
        toolTrends.value = data
      }
    })
  } catch (error) {
    console.error('Error fetching tool trends:', error)
  }
}

const fetchRecentLogs = async () => {
  logsLoading.value = true
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tool-log',
      params: {
        page: 1,
        size: 10
        // 移除call_type过滤，显示所有类型的调用日志
      },
      onSuccess: (data) => {
        recentLogs.value = data
      }
    })
  } catch (error) {
    console.error('Error fetching recent logs:', error)
  } finally {
    logsLoading.value = false
  }
}

const initChart = () => {
  if (!chartContainer.value) return

  chart = echarts.init(chartContainer.value)

  const dates = toolTrends.value.map(item => item.date)
  const totalCalls = toolTrends.value.map(item => item.total_calls)
  const successCalls = toolTrends.value.map(item => item.success_calls)
  const failedCalls = toolTrends.value.map(item => item.failed_calls)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['总调用', '成功调用', '失败调用']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总调用',
        type: 'line',
        data: totalCalls,
        itemStyle: { color: '#1890ff' },
        smooth: true
      },
      {
        name: '成功调用',
        type: 'line',
        data: successCalls,
        itemStyle: { color: '#52c41a' },
        smooth: true
      },
      {
        name: '失败调用',
        type: 'line',
        data: failedCalls,
        itemStyle: { color: '#ff4d4f' },
        smooth: true
      }
    ]
  }

  chart.setOption(option)

  // Handle window resize
  window.addEventListener('resize', () => {
    chart?.resize()
  })
}

const formatDuration = (ms) => {
  if (!ms) return '0ms'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}


</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 8px 0;
}

.stat-number {
  font-size: 20px;
  font-weight: 500;
  color: #1890ff;
}

.stat-number.success {
  color: #52c41a;
}

.stat-label {
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}

/* 最近调用日志表格样式 */
.ant-table-small .ant-table-tbody > tr > td {
  padding: 8px 8px;
}

.ant-table-small .ant-table-thead > tr > th {
  padding: 8px 8px;
  font-weight: 600;
  background: #fafafa;
}
</style>
