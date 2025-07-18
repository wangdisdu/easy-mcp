<template>
  <app-layout current-page-key="func">
    <a-card title="函数管理">
      <div class="action-bar">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索函数名称或描述"
          style="width: 300px"
          @search="handleSearch"
        />

        <a-button type="primary" @click="router.push('/func/create')">
          <template #icon><PlusOutlined /></template>
          创建函数
        </a-button>
      </div>

      <a-table
        :columns="columns"
        :data-source="funcs"
        :loading="loading"
        :pagination="{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          onChange: handlePageChange,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          onShowSizeChange: handlePageSizeChange,
          showTotal: (total) => `共 ${total} 条记录`
        }"
        :row-key="(record) => record.id"
      >
        <!-- 名称列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="router.push(`/func/${record.id}`)">{{ record.name }}</a>
          </template>

          <!-- 描述列 -->
          <template v-else-if="column.key === 'description'">
            <span>{{ record.description || '无描述' }}</span>
          </template>

          <!-- 版本列 -->
          <template v-else-if="column.key === 'version'">
            <a-tag v-if="record.current_version" color="blue">v{{ record.current_version }}</a-tag>
            <span v-else>未发布</span>
          </template>

          <!-- 创建时间列 -->
          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatTimestamp(record.created_at) }}</span>
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space :size="0">
              <a-button type="link" size="small" @click="router.push(`/func/${record.id}/edit`)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除此函数吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(record.id)"
              >
                <a-button type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const loading = ref(false)
const funcs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchText = ref('')

const columns = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
    width: 160,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    width: 200,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '版本',
    key: 'version',
    width: 100,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right'
  }
]

onMounted(() => {
  fetchFuncs()
})

const fetchFuncs = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/func',
      params: {
        page: currentPage.value,
        size: pageSize.value,
        search: searchText.value || undefined
      },
      onSuccess: (data, response) => {
        funcs.value = data
        total.value = response.total
      },
      errorMessage: '获取函数列表失败'
    })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchFuncs()
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  fetchFuncs()
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
  fetchFuncs()
}

const handleDelete = async (id) => {
  try {
    await callApi({
      method: 'delete',
      url: `/api/v1/func/${id}`,
      successMessage: '删除成功',
      errorMessage: '删除失败'
    })

    // Refresh list
    fetchFuncs()
  } catch (error) {
    console.error('Error deleting function:', error)
  }
}
</script>
