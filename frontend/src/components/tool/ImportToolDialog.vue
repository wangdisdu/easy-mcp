<template>
  <a-modal
    :open="visible"
    title="导入内置工具"
    :confirm-loading="loading"
    :width="700"
    @ok="handleImport"
    @cancel="handleCancel"
  >
    <a-spin :spinning="loadingTools">
      <div v-if="builtinTools.length === 0 && !loadingTools" class="empty-state">
        <a-empty description="没有可用的内置工具" />
      </div>
      <a-table
        v-else
        :columns="columns"
        :data-source="builtinTools"
        :pagination="false"
        :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange, type: 'radio' }"
        :row-key="record => record.id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'hasConfig'">
            <a-tag v-if="record.has_config" color="blue">有配置</a-tag>
            <a-tag v-else color="green">无配置</a-tag>
          </template>
        </template>
      </a-table>
    </a-spin>
  </a-modal>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { callApi } from '@/utils/api-util'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

// 监听属性变化
const visibleChanged = (value) => {
  if (!value) {
    selectedRowKeys.value = []
  }
}

const emit = defineEmits(['update:visible', 'imported'])

// 表格列定义
const columns = [
  {
    title: '工具名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description'
  },
  {
    title: '配置',
    key: 'hasConfig'
  }
]

// 数据
const builtinTools = ref([])
const loadingTools = ref(false)
const loading = ref(false)
const selectedRowKeys = ref([])

// 加载内置工具列表
const loadBuiltinTools = async () => {
  loadingTools.value = true
  try {
    await callApi({
      method: 'get',
      url: '/api/v1/tool-builtin',
      onSuccess: (data) => {
        builtinTools.value = data?.tools || []
      }
    })
  } catch (error) {
    console.error('Failed to load builtin tools:', error)
  } finally {
    loadingTools.value = false
  }
}

// 选择变更
const onSelectChange = (keys) => {
  selectedRowKeys.value = keys
}

// 导入工具
const handleImport = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要导入的工具')
    return
  }

  loading.value = true
  try {
    await callApi({
      method: 'post',
      url: '/api/v1/tool-builtin/import',
      data: {
        tool_id: selectedRowKeys.value[0]
      },
      successMessage: '工具导入成功',
      onSuccess: () => {
        emit('imported')
        handleCancel()
      }
    })
  } catch (error) {
    console.error('Failed to import tool:', error)
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  selectedRowKeys.value = []
  emit('update:visible', false)
}

// 组件挂载时的操作
onMounted(() => {
  // 监听属性变化
  visibleChanged(props.visible)

  // 加载内置工具列表
  loadBuiltinTools()
})
</script>

<style scoped>
.empty-state {
  padding: 20px;
  text-align: center;
}
</style>
