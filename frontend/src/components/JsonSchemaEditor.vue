<template>
  <div class="json-schema-editor">
    <div class="editor-mode-switch">
      <a-radio-group v-model:value="editorMode" button-style="solid">
        <a-radio-button value="visual">图形化编辑</a-radio-button>
        <a-radio-button value="json">JSON编辑</a-radio-button>
      </a-radio-group>
    </div>

    <!-- 图形化编辑模式 -->
    <div v-if="editorMode === 'visual'" class="visual-editor">
      <div class="properties-list">
        <div class="properties-header">
          <h3>参数列表</h3>
          <a-button type="primary" size="small" @click="addProperty">
            <template #icon><PlusOutlined /></template>
            添加参数
          </a-button>
        </div>

        <a-empty v-if="!properties.length" description="暂无参数定义" />

        <draggable
          v-else
          v-model="properties"
          item-key="key"
          handle=".drag-handle"
          ghost-class="ghost"
          @end="onDragEnd"
        >
          <template #item="{ element, index }">
            <div class="property-item">
              <div class="property-header">
                <MenuOutlined class="drag-handle" />
                <span class="property-name">{{ element.key }}</span>
                <a-tag color="blue">{{ getTypeLabel(element.schema.type) }}</a-tag>
                <a-tag v-if="element.schema.location" color="purple">{{ element.schema.location }}</a-tag>
                <a-tag v-if="isRequired(element.key)" color="red">必填</a-tag>
                <div class="property-actions">
                  <a-button type="text" size="small" @click="editProperty(index)">
                    <template #icon><EditOutlined /></template>
                  </a-button>
                  <a-button type="text" size="small" @click="removeProperty(index)">
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </div>
              </div>
              <div class="property-description" v-if="element.schema.description">
                {{ element.schema.description }}
              </div>
            </div>
          </template>
        </draggable>
      </div>
    </div>

    <!-- JSON编辑模式 -->
    <div v-else class="json-editor">
      <MonacoEditor
        v-model:value="jsonValue"
        language="json"
        :options="{
          automaticLayout: true,
          scrollBeyondLastLine: false
        }"
        @change="onJsonChange"
      />
    </div>

    <!-- 属性编辑弹窗 -->
    <a-modal
      v-model:open="propertyModalVisible"
      :title="isNewProperty ? '添加参数' : '编辑参数'"
      @ok="saveProperty"
      @cancel="propertyModalVisible = false"
    >
      <a-form :model="currentProperty" layout="vertical">
        <a-form-item label="参数名称" required>
          <a-input
            v-model:value="currentProperty.key"
            placeholder="请输入参数名称"
            :disabled="!isNewProperty"
          />
        </a-form-item>

        <a-form-item label="参数位置" required v-if="isHttpTool">
          <a-select v-model:value="currentProperty.schema.location" placeholder="请选择参数位置">
            <a-select-option value="url">URL</a-select-option>
            <a-select-option value="header">Header</a-select-option>
            <a-select-option value="body">Body</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="参数类型" required>
          <a-select v-model:value="currentProperty.schema.type" placeholder="请选择参数类型">
            <a-select-option value="string">字符串 (string)</a-select-option>
            <a-select-option value="number">数字 (number)</a-select-option>
            <a-select-option value="integer">整数 (integer)</a-select-option>
            <a-select-option value="boolean">布尔值 (boolean)</a-select-option>
            <a-select-option value="array">数组 (array)</a-select-option>
            <a-select-option value="object">对象 (object)</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="描述">
          <a-textarea
            v-model:value="currentProperty.schema.description"
            placeholder="请输入参数描述"
            :rows="2"
          />
        </a-form-item>

        <a-form-item label="是否必填">
          <a-switch v-model:checked="currentProperty.required" />
        </a-form-item>

        <!-- 字符串类型特有属性 -->
        <template v-if="currentProperty.schema.type === 'string'">
          <a-form-item label="默认值">
            <a-input v-model:value="currentProperty.schema.default" placeholder="请输入默认值" />
          </a-form-item>

          <a-form-item label="格式">
            <a-select v-model:value="currentProperty.schema.format" placeholder="请选择格式" allowClear>
              <a-select-option value="email">邮箱 (email)</a-select-option>
              <a-select-option value="uri">URI (uri)</a-select-option>
              <a-select-option value="date">日期 (date)</a-select-option>
              <a-select-option value="date-time">日期时间 (date-time)</a-select-option>
              <a-select-option value="password">密码 (password)</a-select-option>
              <a-select-option value="textarea">文本域 (textarea)</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="枚举值">
            <a-select
              v-model:value="currentProperty.schema.enum"
              mode="tags"
              placeholder="输入后按回车添加枚举值"
              :tokenSeparators="[',']"
            />
          </a-form-item>
        </template>

        <!-- 数字类型特有属性 -->
        <template v-if="currentProperty.schema.type === 'number' || currentProperty.schema.type === 'integer'">
          <a-form-item label="默认值">
            <a-input-number
              v-model:value="currentProperty.schema.default"
              placeholder="请输入默认值"
              :precision="currentProperty.schema.type === 'integer' ? 0 : undefined"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item label="最小值">
            <a-input-number
              v-model:value="currentProperty.schema.minimum"
              placeholder="请输入最小值"
              :precision="currentProperty.schema.type === 'integer' ? 0 : undefined"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item label="最大值">
            <a-input-number
              v-model:value="currentProperty.schema.maximum"
              placeholder="请输入最大值"
              :precision="currentProperty.schema.type === 'integer' ? 0 : undefined"
              style="width: 100%"
            />
          </a-form-item>
        </template>

        <!-- 布尔类型特有属性 -->
        <template v-if="currentProperty.schema.type === 'boolean'">
          <a-form-item label="默认值">
            <a-switch v-model:checked="currentProperty.schema.default" />
          </a-form-item>
        </template>

        <!-- 数组类型特有属性 -->
        <template v-if="currentProperty.schema.type === 'array'">
          <a-form-item label="数组元素类型" required>
            <a-select v-model:value="currentProperty.schema.items.type" placeholder="请选择数组元素类型">
              <a-select-option value="string">字符串 (string)</a-select-option>
              <a-select-option value="number">数字 (number)</a-select-option>
              <a-select-option value="integer">整数 (integer)</a-select-option>
              <a-select-option value="boolean">布尔值 (boolean)</a-select-option>
              <a-select-option value="object">对象 (object)</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="最小元素数量">
            <a-input-number
              v-model:value="currentProperty.schema.minItems"
              placeholder="请输入最小元素数量"
              :min="0"
              :precision="0"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item label="最大元素数量">
            <a-input-number
              v-model:value="currentProperty.schema.maxItems"
              placeholder="请输入最大元素数量"
              :min="0"
              :precision="0"
              style="width: 100%"
            />
          </a-form-item>
        </template>

        <!-- 对象类型特有属性 -->
        <template v-if="currentProperty.schema.type === 'object'">
          <a-alert
            message="对象类型提示"
            description="对象类型参数可以包含嵌套属性，保存后可以在图形化编辑器中单独编辑其属性。"
            type="info"
            show-icon
            style="margin-bottom: 16px"
          />
        </template>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MenuOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import MonacoEditor from './MonacoEditor.vue'
import draggable from 'vuedraggable/src/vuedraggable'

const props = defineProps({
  value: {
    type: String,
    required: true
  },
  isHttpTool: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:value'])

// 编辑模式：visual 或 json
const editorMode = ref('visual')

// JSON编辑器的值
const jsonValue = ref(props.value)

// 解析后的属性列表
const properties = ref([])
const requiredProps = ref([])

// 属性编辑弹窗
const propertyModalVisible = ref(false)
const currentProperty = ref({
  key: '',
  schema: {
    type: 'string',
    description: ''
  },
  required: false
})
const currentPropertyIndex = ref(-1)
const isNewProperty = computed(() => currentPropertyIndex.value === -1)

// 初始化
onMounted(() => {
  parseJsonSchema()
})

// 监听props.value变化
watch(() => props.value, (newValue) => {
  if (newValue !== jsonValue.value) {
    jsonValue.value = newValue
    if (editorMode.value === 'visual') {
      parseJsonSchema()
    }
  }
}, { deep: true })

// 解析JSON Schema
const parseJsonSchema = () => {
  try {
    const schema = JSON.parse(jsonValue.value)

    // 提取属性
    properties.value = []
    if (schema.properties) {
      for (const [key, value] of Object.entries(schema.properties)) {
        properties.value.push({
          key,
          schema: value
        })
      }
    }

    // 提取必填属性
    requiredProps.value = schema.required || []
  } catch (error) {
    message.error('JSON格式错误: ' + error.message)
  }
}

// 生成JSON Schema
const generateJsonSchema = () => {
  const schema = {
    type: 'object',
    properties: {},
    required: [...requiredProps.value]
  }

  // 添加属性
  for (const prop of properties.value) {
    schema.properties[prop.key] = { ...prop.schema }
  }

  return schema
}

// 更新JSON值
const updateJsonValue = () => {
  const schema = generateJsonSchema()
  jsonValue.value = JSON.stringify(schema, null, 2)
  emit('update:value', jsonValue.value)
}

// JSON编辑器变更
const onJsonChange = () => {
  emit('update:value', jsonValue.value)
  if (editorMode.value === 'visual') {
    parseJsonSchema()
  }
}

// 添加属性
const addProperty = () => {
  currentProperty.value = {
    key: '',
    schema: {
      type: 'string',
      description: '',
      location: props.isHttpTool ? 'body' : undefined
    },
    required: false
  }
  currentPropertyIndex.value = -1
  propertyModalVisible.value = true
}

// 编辑属性
const editProperty = (index) => {
  const prop = properties.value[index]
  currentProperty.value = {
    key: prop.key,
    schema: { ...prop.schema },
    required: isRequired(prop.key)
  }
  currentPropertyIndex.value = index
  propertyModalVisible.value = true
}

// 删除属性
const removeProperty = (index) => {
  const key = properties.value[index].key

  // 从必填属性中移除
  const requiredIndex = requiredProps.value.indexOf(key)
  if (requiredIndex !== -1) {
    requiredProps.value.splice(requiredIndex, 1)
  }

  // 移除属性
  properties.value.splice(index, 1)

  // 更新JSON
  updateJsonValue()
}

// 保存属性
const saveProperty = () => {
  if (!currentProperty.value.key) {
    message.error('参数名称不能为空')
    return
  }

  // 检查属性名是否重复
  if (isNewProperty.value) {
    const exists = properties.value.some(p => p.key === currentProperty.value.key)
    if (exists) {
      message.error('参数名称已存在')
      return
    }
  }

  // 处理数组类型，确保items存在
  if (currentProperty.value.schema.type === 'array' && !currentProperty.value.schema.items) {
    currentProperty.value.schema.items = { type: 'string' }
  }

  if (isNewProperty.value) {
    // 添加新属性
    properties.value.push({
      key: currentProperty.value.key,
      schema: { ...currentProperty.value.schema }
    })
  } else {
    // 更新现有属性
    properties.value[currentPropertyIndex.value].schema = { ...currentProperty.value.schema }
  }

  // 更新必填属性
  const requiredIndex = requiredProps.value.indexOf(currentProperty.value.key)
  if (currentProperty.value.required && requiredIndex === -1) {
    requiredProps.value.push(currentProperty.value.key)
  } else if (!currentProperty.value.required && requiredIndex !== -1) {
    requiredProps.value.splice(requiredIndex, 1)
  }

  // 更新JSON
  updateJsonValue()

  // 关闭弹窗
  propertyModalVisible.value = false
}

// 判断属性是否必填
const isRequired = (key) => {
  return requiredProps.value.includes(key)
}

// 获取类型标签
const getTypeLabel = (type) => {
  const typeMap = {
    string: '字符串',
    number: '数字',
    integer: '整数',
    boolean: '布尔值',
    array: '数组',
    object: '对象'
  }
  return typeMap[type] || type
}

// 拖拽结束后更新JSON
const onDragEnd = () => {
  updateJsonValue()
}

// 监听编辑模式变化
watch(editorMode, (newMode) => {
  if (newMode === 'visual') {
    parseJsonSchema()
  }
})

const columns = computed(() => {
  const baseColumns = [
    {
      title: '参数名',
      dataIndex: 'name',
      key: 'name',
      width: '15%'
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: '10%'
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: '20%'
    },
    {
      title: '必填',
      dataIndex: 'required',
      key: 'required',
      width: '8%'
    },
    {
      title: '默认值',
      dataIndex: 'default',
      key: 'default',
      width: '15%'
    },
    {
      title: '操作',
      key: 'action',
      width: '12%'
    }
  ]

  // 检查是否有任何参数包含 location 字段
  const hasLocationField = properties.value.some(param => param.schema.location)
  if (hasLocationField) {
    baseColumns.splice(1, 0, {
      title: '参数位置',
      dataIndex: 'location',
      key: 'location',
      width: '10%'
    })
  }

  return baseColumns
})
</script>

<style scoped>
.json-schema-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 400px;
}

.editor-mode-switch {
  margin-bottom: 6px;
  text-align: right;
}

.visual-editor {
  flex: 1;
  overflow: auto;
  background-color: #fff;
  border-radius: 4px;
}

.json-editor {
  flex: 1;
  height: 400px;
  border-radius: 4px;
  overflow: hidden;
}

.properties-list {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 16px;
  background-color: #fff;
}

.properties-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.properties-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1890ff;
  font-weight: 500;
}

.property-item {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 12px;
  background-color: #fafafa;
}

.property-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.property-name {
  font-weight: 500;
  flex: 1;
}

.property-actions {
  display: flex;
  gap: 4px;
}

.property-description {
  margin-top: 8px;
  color: #666;
  font-size: 13px;
}

.drag-handle {
  cursor: move;
  color: #999;
}

.ghost {
  opacity: 0.5;
  background: #e6f7ff;
  border: 1px dashed #1890ff;
}

/* 弹窗样式 */
:deep(.ant-form-item-label > label) {
  font-weight: 500;
}
</style>