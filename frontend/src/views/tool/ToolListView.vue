<template>
  <app-layout current-page-key="tool">
    <a-card title="工具管理">
      <div class="action-bar">
        <div class="search-filters">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索工具名称或描述"
            style="width: 300px"
            @search="handleSearch"
          />

          <a-select
            v-model:value="selectedTagIds"
            mode="multiple"
            placeholder="按标签筛选"
            style="width: 200px; margin-left: 12px"
            :options="tagOptions"
            @change="handleTagFilter"
            allow-clear
          />
        </div>

        <div>
          <a-dropdown>
            <a-button type="primary" style="margin-right: 8px">
              <template #icon><PlusOutlined /></template>
              创建工具
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="basic" @click="createTool('basic')">
                  <template #icon><ToolOutlined /></template>
                  基础工具
                </a-menu-item>
                <a-menu-item key="http" @click="createTool('http')">
                  <template #icon><GlobalOutlined /></template>
                  HTTP工具
                </a-menu-item>
                <a-menu-item key="database" @click="createTool('database')">
                  <template #icon><DatabaseOutlined /></template>
                  数据库工具
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
          <a-dropdown>
            <a-button>
              <template #icon><ImportOutlined /></template>
              导入工具
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="1" @click="showImportDialog = true">
                  <ApiOutlined />
                  导入内置工具
                </a-menu-item>
                <a-menu-item key="2" @click="router.push('/tool/import-openapi')">
                  <CloudOutlined />
                  导入OpenAPI
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="tools"
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
            <a @click="router.push(`/tool/${record.id}`)" style="display: flex; align-items: center; gap: 6px;">
              <component :is="getToolTypeIcon(record.type)" style="color: #000;" />
              {{ record.name }}
            </a>
          </template>

          <!-- 描述列 -->
          <template v-else-if="column.key === 'description'">
            <span>{{ record.description || '无描述' }}</span>
          </template>



          <!-- 标签列 -->
          <template v-else-if="column.key === 'tags'">
            <div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
              <a-tag
                v-for="tag in record.tags"
                :key="tag.id"
                style="margin: 0"
              >
                {{ tag.name }}
              </a-tag>
              <span v-if="!record.tags || record.tags.length === 0" style="color: #999;">
                无标签
              </span>
              <a-button
                type="text"
                size="small"
                @click="handleManageTags(record)"
                style="margin-left: 4px; padding: 0; height: auto; min-width: auto;"
              >
                <template #icon><EditOutlined /></template>
              </a-button>
            </div>
          </template>

          <!-- 状态列 -->
          <template v-else-if="column.key === 'status'">
            <a-switch
              :checked="record.is_enabled"
              :loading="record.toggling"
              @change="(checked) => handleToggleState(record.id, checked)"
            >
              <template #checkedChildren>启用</template>
              <template #unCheckedChildren>禁用</template>
            </a-switch>
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
              <a-button type="link" size="small" @click="router.push(`/tool/${record.id}/debug`)">
                <template #icon><BugOutlined /></template>
                调试
              </a-button>
              <a-button type="link" size="small" @click="router.push(`/tool/${record.id}/edit`)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除此工具吗？"
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

    <!-- 导入工具对话框 -->
    <import-tool-dialog
      :visible="showImportDialog"
      @update:visible="showImportDialog = $event"
      @imported="fetchTools"
    />

    <!-- 标签管理对话框 -->
    <tool-tag-manager
      v-model:visible="showTagManager"
      :tool-id="selectedToolId"
      @updated="fetchTools"
    />
  </app-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ImportOutlined,
  DownOutlined,
  ToolOutlined,
  ApiOutlined,
  CloudOutlined,
  GlobalOutlined,
  BugOutlined,
  DatabaseOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi, formatTimestamp } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import ImportToolDialog from './ImportToolDialog.vue'
import ToolTagManager from '../../components/ToolTagManager.vue'

const router = useRouter()
const loading = ref(false)
const tools = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchText = ref('')
const showImportDialog = ref(false)
const selectedTagIds = ref([])
const allTags = ref([])
const tagOptions = ref([])
const showTagManager = ref(false)
const selectedToolId = ref(null)

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
    title: '标签',
    key: 'tags',
    width: 200
  },
  {
    title: '状态',
    key: 'status',
    width: 100
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
  fetchTags()
  fetchTools()
})

const fetchTags = async () => {
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tag',
      params: {
        page: 1,
        size: 1000 // 获取所有标签
      },
      onSuccess: (data) => {
        allTags.value = data
        tagOptions.value = data.map(tag => ({
          label: tag.name,
          value: tag.id
        }))
      },
      errorMessage: '获取标签列表失败'
    })
  } catch (error) {
    console.error('Error fetching tags:', error)
  }
}

const fetchTools = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tool',
      params: {
        page: currentPage.value,
        size: pageSize.value,
        search: searchText.value || undefined,
        ...(selectedTagIds.value.length > 0 && {
          tag_ids: selectedTagIds.value.join(',')
        })
      },
      onSuccess: (data, response) => {
        tools.value = data
        total.value = response.total
      },
      errorMessage: '获取工具列表失败'
    })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTools()
}

const handleTagFilter = () => {
  currentPage.value = 1
  fetchTools()
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  fetchTools()
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
  fetchTools()
}

const handleDelete = async (id) => {
  try {
    await callApi({
      method: 'delete',
      url: `/api/v1/tool/${id}`,
      successMessage: '删除成功',
      errorMessage: '删除失败'
    })

    // Refresh list
    fetchTools()
  } catch (error) {
    console.error('Error deleting tool:', error)
  }
}

const handleToggleState = async (id, enable) => {
  // 设置加载状态
  const tool = tools.value.find(t => t.id === id)
  if (tool) {
    tool.toggling = true
  }

  try {
    const action = enable ? 'enable' : 'disable'
    await callApi({
      method: 'patch',
      url: `/api/v1/tool/${id}/${action}`,
      successMessage: `${enable ? '启用' : '禁用'}成功`,
      errorMessage: `${enable ? '启用' : '禁用'}失败`
    })

    // Refresh list
    fetchTools()
  } catch (error) {
    console.error(`Error ${enable ? 'enabling' : 'disabling'} tool:`, error)
  } finally {
    // 清除加载状态
    if (tool) {
      tool.toggling = false
    }
  }
}

const createTool = (type) => {
  router.push(`/tool/create?type=${type}`)
}

const getToolTypeColor = (type) => {
  switch (type) {
    case 'http':
      return 'blue'
    case 'database':
      return 'purple'
    default:
      return 'green'
  }
}

const getToolTypeName = (type) => {
  switch (type) {
    case 'http':
      return 'HTTP工具'
    case 'database':
      return '数据库工具'
    default:
      return '基础工具'
  }
}

const getToolTypeIcon = (type) => {
  switch (type) {
    case 'http':
      return GlobalOutlined
    case 'database':
      return DatabaseOutlined
    default:
      return ToolOutlined
  }
}



const handleManageTags = (tool) => {
  selectedToolId.value = tool.id
  showTagManager.value = true
}
</script>

<style scoped>
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.search-filters {
  display: flex;
  align-items: center;
}
</style>
