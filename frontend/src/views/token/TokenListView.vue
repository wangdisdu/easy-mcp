<template>
  <app-layout current-page-key="token">
    <a-card title="MCP 访问令牌">
      <a-alert
        type="info"
        show-icon
        style="margin-bottom: 16px"
        message="MCP 端点鉴权说明"
        description="系统中没有任何令牌时，MCP 端点（SSE / Streamable HTTP）保持开放、不鉴权；一旦创建了令牌，所有 MCP 请求必须携带 Authorization: Bearer <token>，且只能访问该令牌绑定的工具。令牌不支持禁用，吊销请直接删除；删除全部令牌即关闭鉴权。"
      />

      <div class="action-bar">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索令牌名称或描述"
          style="width: 300px"
          @search="handleSearch"
        />

        <a-button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          创建令牌
        </a-button>
      </div>

      <a-table
        :columns="columns"
        :data-source="tokens"
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
          <template v-if="column.key === 'name'">
            <strong>{{ record.name }}</strong>
          </template>

          <template v-else-if="column.key === 'description'">
            <span>{{ record.description || '无描述' }}</span>
          </template>

          <template v-else-if="column.key === 'token'">
            <a-space>
              <a-typography-text code>
                {{ revealed[record.id] ? record.token : maskToken(record.token) }}
              </a-typography-text>
              <a-button type="link" size="small" @click="toggleReveal(record.id)">
                {{ revealed[record.id] ? '隐藏' : '显示' }}
              </a-button>
              <a-button type="link" size="small" @click="copyToken(record.token)">
                <template #icon><CopyOutlined /></template>
                复制
              </a-button>
            </a-space>
          </template>

          <template v-else-if="column.key === 'tool_count'">
            <a-badge
              :count="record.tool_ids ? record.tool_ids.length : 0"
              :number-style="{ backgroundColor: '#52c41a' }"
              show-zero
            />
          </template>

          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatTimestamp(record.created_at) }}</span>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space :size="0">
              <a-button type="link" size="small" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除此令牌吗？使用该令牌的 MCP 客户端将立即失效。"
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

    <!-- 创建/编辑令牌对话框 -->
    <a-modal
      v-model:open="showModal"
      :title="editingToken ? '编辑令牌' : '创建令牌'"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitting"
      ok-text="确定"
      cancel-text="取消"
      width="600px"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item label="令牌名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入令牌名称" />
        </a-form-item>

        <a-form-item label="令牌描述" name="description">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入令牌描述（可选）"
            :rows="2"
          />
        </a-form-item>

        <a-form-item
          label="绑定工具"
          name="tool_ids"
          extra="该令牌仅可列出/调用所绑定的工具；不绑定任何工具则该令牌无任何工具权限。"
        >
          <a-select
            v-model:value="formData.tool_ids"
            mode="multiple"
            placeholder="选择该令牌可访问的工具"
            :options="toolOptions"
            :loading="toolsLoading"
            option-filter-prop="label"
            allow-clear
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 新令牌创建成功提示 -->
    <a-modal
      v-model:open="showCreatedModal"
      title="令牌创建成功"
      :footer="null"
      width="600px"
    >
      <a-alert
        type="warning"
        show-icon
        style="margin-bottom: 12px"
        message="请妥善保管该令牌，并配置到 MCP 客户端的 Authorization: Bearer 头中。"
      />
      <a-typography-paragraph :copyable="{ text: createdToken }" code>
        {{ createdToken }}
      </a-typography-paragraph>
    </a-modal>
  </app-layout>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const loading = ref(false)
const tokens = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchText = ref('')
const showModal = ref(false)
const submitting = ref(false)
const editingToken = ref(null)
const formRef = ref()
const revealed = reactive({})

const toolOptions = ref([])
const toolsLoading = ref(false)

const showCreatedModal = ref(false)
const createdToken = ref('')

const formData = reactive({
  name: '',
  description: '',
  tool_ids: []
})

const rules = {
  name: [
    { required: true, message: '请输入令牌名称', trigger: 'blur' },
    { min: 1, max: 50, message: '令牌名称长度应在1-50个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述长度不能超过500个字符', trigger: 'blur' }
  ]
}

const columns = [
  { title: '名称', key: 'name', width: 140 },
  { title: '描述', key: 'description', width: 160, ellipsis: true },
  { title: '令牌', key: 'token', width: 280 },
  { title: '绑定工具数', key: 'tool_count', width: 100, align: 'center' },
  { title: '创建时间', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 140, fixed: 'right' }
]

const maskToken = (token) => {
  if (!token) return ''
  if (token.length <= 12) return token
  return `${token.slice(0, 8)}…${token.slice(-4)}`
}

const toggleReveal = (id) => {
  revealed[id] = !revealed[id]
}

const copyToken = async (token) => {
  try {
    await navigator.clipboard.writeText(token)
    message.success('已复制到剪贴板')
  } catch (e) {
    message.error('复制失败，请手动选择复制')
  }
}

onMounted(() => {
  fetchTokens()
  fetchTools()
})

const fetchTokens = async () => {
  loading.value = true
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/token',
      params: {
        page: currentPage.value,
        size: pageSize.value,
        search: searchText.value || undefined
      },
      onSuccess: (data, response) => {
        tokens.value = data
        total.value = response.total
      },
      errorMessage: '获取令牌列表失败'
    })
  } finally {
    loading.value = false
  }
}

const fetchTools = async () => {
  toolsLoading.value = true
  try {
    const pageSize = 100
    let page = 1
    let total = 0
    const options = []

    do {
      let pageData = []
      await callApi({
        method: 'get',
        url: '/api/v1/tool',
        params: { page, size: pageSize },
        onSuccess: (data, response) => {
          pageData = data || []
          total = response.total || 0
        },
        errorMessage: '获取工具列表失败'
      })

      if (pageData.length === 0) break
      options.push(...pageData.map((t) => ({ label: t.name, value: t.id })))
      page += 1
    } while (options.length < total)

    toolOptions.value = options
  } finally {
    toolsLoading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTokens()
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  fetchTokens()
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
  fetchTokens()
}

const handleCreate = () => {
  editingToken.value = null
  formData.name = ''
  formData.description = ''
  formData.tool_ids = []
  showModal.value = true
}

const handleEdit = (token) => {
  editingToken.value = token
  formData.name = token.name
  formData.description = token.description || ''
  formData.tool_ids = [...(token.tool_ids || [])]
  showModal.value = true
}

const handleCancel = () => {
  showModal.value = false
  editingToken.value = null
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const isEdit = !!editingToken.value
    const url = isEdit
      ? `/api/v1/token/${editingToken.value.id}`
      : '/api/v1/token'
    const method = isEdit ? 'put' : 'post'

    const data = {
      name: formData.name,
      description: formData.description || null,
      tool_ids: formData.tool_ids
    }

    await callApi({
      method,
      url,
      data,
      successMessage: isEdit ? '更新成功' : '创建成功',
      errorMessage: isEdit ? '更新失败' : '创建失败',
      onSuccess: (created) => {
        if (!isEdit && created?.token) {
          createdToken.value = created.token
          showCreatedModal.value = true
        }
      }
    })

    handleCancel()
    fetchTokens()
  } catch (error) {
    console.error('Error submitting token:', error)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await callApi({
      method: 'delete',
      url: `/api/v1/token/${id}`,
      successMessage: '删除成功',
      errorMessage: '删除失败'
    })
    fetchTokens()
  } catch (error) {
    console.error('Error deleting token:', error)
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
