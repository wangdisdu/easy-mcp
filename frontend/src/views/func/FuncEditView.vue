<template>
  <app-layout current-page-key="func">
    <a-card :title="isEdit ? '编辑函数' : '创建函数'">
      <template #extra>
        <a-space>
          <a-button @click="goBack">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button type="primary" @click="handleSave" :loading="saving">
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
          <a-button type="primary" @click="handleSaveAndDeploy" :loading="saving">
            <template #icon><CloudUploadOutlined /></template>
            {{ isEdit ? '保存并发布' : '创建并发布' }}
          </a-button>
        </a-space>
      </template>

      <a-form
        :model="formState"
        layout="vertical"
        class="form-container"
      >
        <a-form-item label="函数名称" required>
          <a-input v-model:value="formState.name" placeholder="请输入函数名称" />
        </a-form-item>

        <a-form-item label="函数描述">
          <a-textarea v-model:value="formState.description" placeholder="请输入函数描述" :rows="3" />
        </a-form-item>

        <a-form-item label="依赖函数">
          <a-select
            v-model:value="formState.depend_ids"
            mode="multiple"
            placeholder="请选择依赖函数"
            :loading="loadingFuncs"
            :options="funcOptions"
          />
        </a-form-item>

        <a-form-item label="函数代码" required>
          <div class="editor-container">
            <MonacoEditor
              v-model:value="formState.code"
              language="python"
              :options="{
                automaticLayout: true,
                scrollBeyondLastLine: false
              }"
            />
          </div>
        </a-form-item>
      </a-form>
    </a-card>
  </app-layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  SaveOutlined,
  RollbackOutlined,
  CloudUploadOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'
import MonacoEditor from '../../components/MonacoEditor.vue'

const router = useRouter()
const route = useRoute()
const funcId = computed(() => route.params.id)
const isEdit = computed(() => !!funcId.value)

const saving = ref(false)
const loading = ref(false)
const loadingFuncs = ref(false)

const formState = reactive({
  name: '',
  description: '',
  code: '# 函数实现代码\n\ndef my_function(param1, param2):\n    """函数文档\n    \n    Args:\n        param1: 参数1\n        param2: 参数2\n        \n    Returns:\n        返回值\n    """\n    return param1 + param2\n',
  depend_ids: []
})

const funcOptions = ref([])

onMounted(async () => {
  // Load functions
  await fetchFunctions()

  // If editing, load function data
  if (isEdit.value) {
    await fetchFuncData()
  }
})

const fetchFunctions = async () => {
  loadingFuncs.value = true

  try {
    await callApi({
      method: 'get',
      url: '/api/v1/func',
      params: { page: 1, size: 100 },
      onSuccess: (data) => {
        // Filter out current function if editing
        const filteredFuncs = isEdit.value
          ? data.filter(func => func.id !== parseInt(funcId.value))
          : data

        funcOptions.value = filteredFuncs.map(func => ({
          value: func.id,
          label: func.name
        }))
      },
      errorMessage: '获取函数列表失败'
    })
  } finally {
    loadingFuncs.value = false
  }
}

const fetchFuncData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/func/${funcId.value}`,
      onSuccess: (data) => {
        formState.name = data.name
        formState.description = data.description || ''
        formState.code = data.code

        // Load dependencies
        fetchFuncDependencies()
      },
      errorMessage: '获取函数数据失败'
    })
  } finally {
    loading.value = false
  }
}

const fetchFuncDependencies = async () => {
  try {
    await callApi({
      method: 'get',
      url: `/api/v1/func/${funcId.value}/depend`,
      onSuccess: (data) => {
        if (data && Array.isArray(data)) {
          formState.depend_ids = data.map(func => func.id)
        } else {
          formState.depend_ids = []
        }
      },
      errorMessage: '获取函数依赖关系失败'
    })
  } catch (error) {
    console.error('Error fetching function dependencies:', error)
  }
}

const validateForm = () => {
  if (!formState.name) {
    message.error('请输入函数名称')
    return false
  }

  if (!formState.code) {
    message.error('请输入函数代码')
    return false
  }

  return true
}

const prepareData = () => {
  return {
    name: formState.name,
    description: formState.description,
    code: formState.code,
    depend_ids: formState.depend_ids
  }
}

const handleSave = async () => {
  if (!validateForm()) return

  saving.value = true

  try {
    const data = prepareData()

    if (isEdit.value) {
      await callApi({
        method: 'put',
        url: `/api/v1/func/${funcId.value}`,
        data,
        successMessage: '保存成功',
        errorMessage: '保存失败',
        onSuccess: () => {
          goBack()
        }
      })
    } else {
      await callApi({
        method: 'post',
        url: '/api/v1/func',
        data,
        successMessage: '创建成功',
        errorMessage: '创建失败',
        onSuccess: () => {
          goBack()
        }
      })
    }
  } finally {
    saving.value = false
  }
}

const handleSaveAndDeploy = async () => {
  if (!validateForm()) return

  saving.value = true

  try {
    const data = prepareData()

    if (isEdit.value) {
      // 编辑模式：保存并发布
      await callApi({
        method: 'put',
        url: `/api/v1/func/${funcId.value}/deploy`,
        data,
        successMessage: '保存并发布成功',
        errorMessage: '保存并发布失败',
        onSuccess: () => {
          goBack()
        }
      })
    } else {
      // 创建模式：创建并发布
      await callApi({
        method: 'post',
        url: '/api/v1/func/deploy',
        data,
        successMessage: '创建并发布成功',
        errorMessage: '创建并发布失败',
        onSuccess: () => {
          goBack()
        }
      })
    }
  } finally {
    saving.value = false
  }
}

const goBack = () => {
  router.back()
}
</script>
