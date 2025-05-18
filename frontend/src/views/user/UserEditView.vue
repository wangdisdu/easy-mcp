<template>
  <app-layout current-page-key="user">
    <a-card :title="isEdit ? '编辑用户' : '创建用户'">
      <template #extra>
        <a-space>
          <a-button @click="goBack">
            <template #icon><RollbackOutlined /></template>
            返回
          </a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
        </a-space>
      </template>

      <a-form
        :model="formState"
        layout="vertical"
        class="form-container"
      >
        <a-form-item v-if="!isEdit" label="用户名" required>
          <a-input v-model:value="formState.username" placeholder="请输入用户名" />
        </a-form-item>

        <a-form-item v-else label="用户名">
          <a-input v-model:value="formState.username" disabled />
        </a-form-item>

        <a-form-item label="邮箱" required>
          <a-input v-model:value="formState.email" placeholder="请输入邮箱" />
        </a-form-item>

        <a-form-item :label="isEdit ? '新密码（留空不修改）' : '密码'" :required="!isEdit">
          <a-input-password v-model:value="formState.password" placeholder="请输入密码" />
        </a-form-item>

        <a-form-item :label="isEdit ? '确认新密码' : '确认密码'" :required="!isEdit">
          <a-input-password v-model:value="formState.confirmPassword" placeholder="请再次输入密码" />
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
  RollbackOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { callApi } from '../../utils/api-util'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const route = useRoute()
const userId = computed(() => route.params.id)
const isEdit = computed(() => !!userId.value)

const saving = ref(false)
const loading = ref(false)

const formState = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

onMounted(() => {
  // If editing, load user data
  if (isEdit.value) {
    fetchUserData()
  }
})

const fetchUserData = async () => {
  loading.value = true

  try {
    await callApi({
      method: 'get',
      url: `/api/v1/user/${userId.value}`,
      onSuccess: (data) => {
        formState.username = data.username
        formState.email = data.email
      },
      errorMessage: '获取用户数据失败'
    })
  } finally {
    loading.value = false
  }
}

const validateForm = () => {
  if (!isEdit.value && !formState.username) {
    message.error('请输入用户名')
    return false
  }

  if (!formState.email) {
    message.error('请输入邮箱')
    return false
  }

  // Email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(formState.email)) {
    message.error('请输入有效的邮箱地址')
    return false
  }

  // Password validation for new user
  if (!isEdit.value && !formState.password) {
    message.error('请输入密码')
    return false
  }

  // Password confirmation
  if (formState.password && formState.password !== formState.confirmPassword) {
    message.error('两次输入的密码不一致')
    return false
  }

  return true
}

const prepareData = () => {
  const data = {
    email: formState.email
  }

  if (!isEdit.value) {
    data.username = formState.username
    data.password = formState.password
  } else if (formState.password) {
    data.password = formState.password
  }

  return data
}

const handleSave = async () => {
  if (!validateForm()) return

  saving.value = true

  try {
    const data = prepareData()

    if (isEdit.value) {
      await callApi({
        method: 'put',
        url: `/api/v1/user/${userId.value}`,
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
        url: '/api/v1/user',
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

const goBack = () => {
  router.back()
}
</script>
