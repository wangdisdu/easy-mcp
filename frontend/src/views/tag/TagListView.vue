<template>
  <app-layout current-page-key="tag">
    <a-card title="标签管理">
      <div class="action-bar">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索标签名称或描述"
          style="width: 300px"
          @search="handleSearch"
        />

        <a-button type="primary" @click="showCreateModal = true">
          <template #icon><PlusOutlined /></template>
          创建标签
        </a-button>
      </div>

      <a-table
        :columns="columns"
        :data-source="tags"
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
        <template #bodyCell="{ column, record }">
          <!-- 标签名称列 -->
          <template v-if="column.key === 'name'">
            <a-tag style="margin: 0">
              {{ record.name }}
            </a-tag>
          </template>

          <!-- 描述列 -->
          <template v-else-if="column.key === 'description'">
            <span>{{ record.description || '无描述' }}</span>
          </template>

          <!-- 工具数量列 -->
          <template v-else-if="column.key === 'tool_count'">
            <a-badge :count="record.tool_count" :number-style="{ backgroundColor: '#52c41a' }" />
          </template>

          <!-- 创建时间列 -->
          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatTimestamp(record.created_at) }}</span>
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space :size="0">
              <a-button type="link" size="small" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除此标签吗？"
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

    <!-- 创建/编辑标签对话框 -->
    <a-modal
      v-model:open="showCreateModal"
      :title="editingTag ? '编辑标签' : '创建标签'"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitting"
      ok-text="确定"
      cancel-text="取消"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item label="标签名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入标签名称" />
        </a-form-item>

        <a-form-item label="标签描述" name="description">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入标签描述（可选）"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </app-layout>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const loading = ref(false)
const tags = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchText = ref('')
const showCreateModal = ref(false)
const submitting = ref(false)
const editingTag = ref(null)
const formRef = ref()

const formData = reactive({
  name: '',
  description: ''
})

const rules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 1, max: 50, message: '标签名称长度应在1-50个字符之间', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9]+$/, message: '标签名称只能包含字母和数字', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述长度不能超过500个字符', trigger: 'blur' }
  ]
}

const columns = [
  {
    title: '标签名称',
    key: 'name',
    width: 150
  },
  {
    title: '描述',
    key: 'description',
    width: 200,
    ellipsis: true,
    tooltip: true
  },
  {
    title: '关联工具数',
    key: 'tool_count',
    width: 120,
    align: 'center'
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right'
  }
]

onMounted(() => {
  fetchTags()
})

const fetchTags = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tag/with-count',
      params: {
        page: currentPage.value,
        size: pageSize.value,
        search: searchText.value || undefined
      },
      onSuccess: (data, response) => {
        tags.value = data
        total.value = response.total
      },
      errorMessage: '获取标签列表失败'
    })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTags()
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  fetchTags()
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
  fetchTags()
}

const handleEdit = (tag) => {
  editingTag.value = tag
  formData.name = tag.name
  formData.description = tag.description || ''
  showCreateModal.value = true
}

const handleCancel = () => {
  showCreateModal.value = false
  editingTag.value = null
  formData.name = ''
  formData.description = ''
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const url = editingTag.value
      ? `/api/v1/tag/${editingTag.value.id}`
      : '/api/v1/tag'
    const method = editingTag.value ? 'put' : 'post'

    await callApi({
      method,
      url,
      data: {
        name: formData.name,
        description: formData.description || null
      },
      successMessage: editingTag.value ? '更新成功' : '创建成功',
      errorMessage: editingTag.value ? '更新失败' : '创建失败'
    })

    handleCancel()
    fetchTags()
  } catch (error) {
    console.error('Error submitting tag:', error)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await callApi({
      method: 'delete',
      url: `/api/v1/tag/${id}`,
      successMessage: '删除成功',
      errorMessage: '删除失败'
    })

    fetchTags()
  } catch (error) {
    console.error('Error deleting tag:', error)
  }
}
</script>

<style scoped>
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
