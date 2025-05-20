<template>
  <div class="json-schema-form">
    <a-form
      :model="formData"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      @finish="handleSubmit"
    >
      <template v-for="(field, key) in schemaFields" :key="key">
        <!-- 文本输入框 -->
        <a-form-item
          v-if="field.type === 'string' && !field.enum && !field.format"
          :label="field.title || key"
          :name="key"
          :rules="[{ required: field.required, message: `请输入${field.title || key}` }]"
          :help="field.description"
        >
          <a-input
            v-model:value="formData[key]"
            :placeholder="field.placeholder || `请输入${field.title || key}`"
          />
        </a-form-item>

        <!-- 数字输入框 -->
        <a-form-item
          v-else-if="field.type === 'number' || field.type === 'integer'"
          :label="field.title || key"
          :name="key"
          :rules="[{ required: field.required, message: `请输入${field.title || key}` }]"
          :help="field.description"
        >
          <a-input-number
            v-model:value="formData[key]"
            :min="field.minimum"
            :max="field.maximum"
            :step="field.type === 'integer' ? 1 : 0.1"
            style="width: 100%"
          />
        </a-form-item>

        <!-- 下拉选择框 -->
        <a-form-item
          v-else-if="field.enum"
          :label="field.title || key"
          :name="key"
          :rules="[{ required: field.required, message: `请选择${field.title || key}` }]"
          :help="field.description"
        >
          <a-select
            v-model:value="formData[key]"
            :placeholder="`请选择${field.title || key}`"
            style="width: 100%"
          >
            <a-select-option
              v-for="(option, index) in field.enum"
              :key="index"
              :value="option"
            >
              {{ field.enumNames && field.enumNames[index] ? field.enumNames[index] : option }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- 布尔值开关 -->
        <a-form-item
          v-else-if="field.type === 'boolean'"
          :label="field.title || key"
          :name="key"
          :help="field.description"
        >
          <a-switch v-model:checked="formData[key]" />
        </a-form-item>

        <!-- 日期选择器 -->
        <a-form-item
          v-else-if="field.format === 'date'"
          :label="field.title || key"
          :name="key"
          :rules="[{ required: field.required, message: `请选择${field.title || key}` }]"
          :help="field.description"
        >
          <a-date-picker
            v-model:value="formData[key]"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </a-form-item>

        <!-- 日期时间选择器 -->
        <a-form-item
          v-else-if="field.format === 'date-time'"
          :label="field.title || key"
          :name="key"
          :rules="[{ required: field.required, message: `请选择${field.title || key}` }]"
          :help="field.description"
        >
          <a-date-picker
            v-model:value="formData[key]"
            show-time
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </a-form-item>

        <!-- 文本域 -->
        <a-form-item
          v-else-if="field.format === 'textarea'"
          :label="field.title || key"
          :name="key"
          :rules="[{ required: field.required, message: `请输入${field.title || key}` }]"
          :help="field.description"
        >
          <a-textarea
            v-model:value="formData[key]"
            :placeholder="field.placeholder || `请输入${field.title || key}`"
            :rows="4"
          />
        </a-form-item>

        <!-- 默认文本输入 -->
        <a-form-item
          v-else
          :label="field.title || key"
          :name="key"
          :rules="[{ required: field.required, message: `请输入${field.title || key}` }]"
          :help="field.description"
        >
          <a-input
            v-model:value="formData[key]"
            :placeholder="field.placeholder || `请输入${field.title || key}`"
          />
        </a-form-item>
      </template>

      <a-form-item :wrapper-col="{ span: 18, offset: 6 }">
        <a-button type="primary" html-type="submit" :loading="loading">保存</a-button>
        <a-button style="margin-left: 10px" @click="handleCancel">取消</a-button>
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  schema: {
    type: Object,
    required: true
  },
  value: {
    type: Object,
    default: () => ({})
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:value', 'submit', 'cancel'])

// 表单数据
const formData = ref({})

// 解析 JSON Schema 中的字段
const schemaFields = computed(() => {
  const fields = {}
  
  if (props.schema && props.schema.properties) {
    Object.keys(props.schema.properties).forEach(key => {
      const property = props.schema.properties[key]
      fields[key] = {
        ...property,
        required: props.schema.required && props.schema.required.includes(key)
      }
    })
  }
  
  return fields
})

// 初始化表单数据
const initFormData = () => {
  const data = { ...props.value }
  
  // 为每个字段设置默认值
  if (props.schema && props.schema.properties) {
    Object.keys(props.schema.properties).forEach(key => {
      const property = props.schema.properties[key]
      
      // 如果值不存在，使用默认值
      if (data[key] === undefined && property.default !== undefined) {
        data[key] = property.default
      }
      
      // 如果仍然不存在，根据类型设置空值
      if (data[key] === undefined) {
        if (property.type === 'string') {
          data[key] = ''
        } else if (property.type === 'number' || property.type === 'integer') {
          data[key] = null
        } else if (property.type === 'boolean') {
          data[key] = false
        } else if (property.type === 'array') {
          data[key] = []
        } else if (property.type === 'object') {
          data[key] = {}
        }
      }
    })
  }
  
  formData.value = data
}

// 处理表单提交
const handleSubmit = () => {
  emit('update:value', formData.value)
  emit('submit', formData.value)
}

// 处理取消
const handleCancel = () => {
  emit('cancel')
}

// 监听 value 变化
watch(() => props.value, () => {
  initFormData()
}, { deep: true })

// 监听 schema 变化
watch(() => props.schema, () => {
  initFormData()
}, { deep: true })

// 组件挂载时初始化
onMounted(() => {
  initFormData()
})
</script>

<style>
.json-schema-form {
  max-width: 800px;
  margin: 0 auto;
}
</style>
