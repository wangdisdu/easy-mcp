<template>
  <a-modal
    :open="visible"
    title="管理工具标签"
    @ok="handleSubmit"
    @cancel="handleCancel"
    :confirm-loading="submitting"
    width="600px"
    ok-text="确定"
    cancel-text="取消"
  >
    <div class="tag-manager">
      <div class="current-tags">
        <h4>当前标签</h4>
        <div class="tag-list">
          <a-tag
            v-for="tag in currentTags"
            :key="tag.id"
            closable
            @close="removeTag(tag.id)"
          >
            {{ tag.name }}
          </a-tag>
          <span v-if="currentTags.length === 0" class="empty-text">
            暂无标签
          </span>
        </div>
      </div>

      <a-divider />

      <div class="available-tags">
        <h4>可用标签</h4>
        <div class="tag-search">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索标签"
            style="margin-bottom: 12px"
            @search="filterTags"
          />
        </div>
        <div class="tag-list">
          <a-tag
            v-for="tag in filteredAvailableTags"
            :key="tag.id"
            style="cursor: pointer; margin-bottom: 8px"
            @click="addTag(tag)"
          >
            <template #icon><PlusOutlined /></template>
            {{ tag.name }}
          </a-tag>
          <span v-if="filteredAvailableTags.length === 0" class="empty-text">
            没有可添加的标签
          </span>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi } from '../utils/api-util'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  toolId: {
    type: [Number, null],
    default: null
  }
})

const emit = defineEmits(['update:visible', 'updated'])

const submitting = ref(false)
const searchText = ref('')
const currentTags = ref([])
const allTags = ref([])
const originalTagIds = ref([])

// 计算可用标签（排除已选择的）
const availableTags = computed(() => {
  const currentTagIds = currentTags.value.map(tag => tag.id)
  return allTags.value.filter(tag => !currentTagIds.includes(tag.id))
})

// 过滤后的可用标签
const filteredAvailableTags = computed(() => {
  if (!searchText.value) {
    return availableTags.value
  }
  return availableTags.value.filter(tag =>
    tag.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
    (tag.description && tag.description.toLowerCase().includes(searchText.value.toLowerCase()))
  )
})

// 监听visible变化，加载数据
watch(() => props.visible, (newVal) => {
  if (newVal && props.toolId) {
    loadData()
  }
})

const loadData = async () => {
  if (!props.toolId) {
    return
  }

  try {
    // 加载所有标签
    await callApi({
      method: 'get',
      url: '/api/v1/tag',
      params: { page: 1, size: 1000 },
      onSuccess: (data) => {
        allTags.value = data
      },
      errorMessage: '获取标签列表失败'
    })

    // 加载工具当前标签
    await callApi({
      method: 'get',
      url: `/api/v1/tool/${props.toolId}/tags`,
      onSuccess: (data) => {
        currentTags.value = data
        originalTagIds.value = data.map(tag => tag.id)
      },
      errorMessage: '获取工具标签失败'
    })
  } catch (error) {
    console.error('Error loading data:', error)
  }
}

const addTag = (tag) => {
  if (!currentTags.value.find(t => t.id === tag.id)) {
    currentTags.value.push(tag)
  }
}

const removeTag = (tagId) => {
  currentTags.value = currentTags.value.filter(tag => tag.id !== tagId)
}

const filterTags = () => {
  // 搜索功能通过computed属性实现，这里不需要额外逻辑
}

const handleSubmit = async () => {
  if (!props.toolId) {
    return
  }

  try {
    submitting.value = true

    const currentTagIds = currentTags.value.map(tag => tag.id)

    await callApi({
      method: 'put',
      url: `/api/v1/tool/${props.toolId}/tags`,
      data: {
        tag_ids: currentTagIds
      },
      successMessage: '标签更新成功',
      errorMessage: '标签更新失败'
    })

    emit('updated')
    handleCancel()
  } catch (error) {
    console.error('Error updating tags:', error)
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  emit('update:visible', false)
  searchText.value = ''
  currentTags.value = []
  allTags.value = []
  originalTagIds.value = []
}
</script>

<style scoped>
.tag-manager {
  max-height: 500px;
  overflow-y: auto;
}

.current-tags,
.available-tags {
  margin-bottom: 16px;
}

.tag-list {
  min-height: 40px;
  padding: 8px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  background-color: #fafafa;
}

.tag-list .ant-tag {
  margin-bottom: 8px;
}

.empty-text {
  color: #999;
  font-style: italic;
}

h4 {
  margin-bottom: 8px;
  font-weight: 600;
}
</style>
