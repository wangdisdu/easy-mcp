<template>
  <div class="monaco-editor-wrapper">
    <div v-if="loading" class="monaco-editor-loading">
      <a-spin tip="加载编辑器中..."></a-spin>
    </div>
    <div ref="editorContainer" class="monaco-editor-container" :style="{ height: height }"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick, defineExpose } from 'vue'
import { Spin as ASpin } from 'ant-design-vue'
import * as monaco from 'monaco-editor'
import { initMonacoWorkers } from '../utils/monaco-config'

const props = defineProps({
  value: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'javascript'
  },
  options: {
    type: Object,
    default: () => ({})
  },
  height: {
    type: String,
    default: '400px'
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:value', 'editor-mounted'])

const editorContainer = ref(null)
const loading = ref(true)
let editor = null
let resizeObserver = null
let contentChangeDisposable = null

// 初始化编辑器
const initEditor = async () => {
  if (!editorContainer.value || editor) return

  // 确保 Monaco workers 已初始化
  initMonacoWorkers()

  // 创建编辑器并合并选项
  editor = monaco.editor.create(editorContainer.value, {
    value: props.value,
    language: props.language,
    theme: 'vs',
    automaticLayout: false, // 手动处理布局以提高性能
    scrollBeyondLastLine: false,
    minimap: { enabled: false },
    readOnly: props.readOnly,
    ...props.options
  })

  // 监听变化
  contentChangeDisposable = editor.onDidChangeModelContent(() => {
    const value = editor.getValue()
    emit('update:value', value)
  })

  // 添加容器大小变化监听
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      if (editor) {
        editor.layout()
      }
    })
    resizeObserver.observe(editorContainer.value)
  } else {
    // 兼容旧浏览器
    window.addEventListener('resize', handleResize)
  }

  // 触发编辑器挂载事件
  emit('editor-mounted', editor)

  // 隐藏加载指示器
  loading.value = false
}

// 处理窗口大小变化
const handleResize = () => {
  if (editor) {
    editor.layout()
  }
}

// 使用 Monaco 的内置格式化器格式化代码
const formatCode = async () => {
  if (!editor) return false

  try {
    await editor.getAction('editor.action.formatDocument').run()
    return true
  } catch (error) {
    console.error('格式化代码时出错:', error)
    return false
  }
}

// 设置光标位置
const setCursorPosition = (lineNumber, column = 1) => {
  if (!editor) return

  editor.setPosition({ lineNumber, column })
  editor.revealPositionInCenter({ lineNumber, column })
  editor.focus()
}

// 获取当前编辑器实例
const getEditor = () => editor

onMounted(async () => {
  // 使用 nextTick 确保 DOM 已完全渲染
  await nextTick()
  initEditor()
})

onBeforeUnmount(() => {
  // 移除事件监听器和观察器
  window.removeEventListener('resize', handleResize)

  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }

  if (contentChangeDisposable) {
    contentChangeDisposable.dispose()
    contentChangeDisposable = null
  }

  // 释放编辑器
  if (editor) {
    editor.dispose()
    editor = null
  }
})

// 当 props.value 变化时更新编辑器值
watch(
  () => props.value,
  (newValue) => {
    if (editor && newValue !== editor.getValue()) {
      // 保存光标位置
      const position = editor.getPosition()

      // 更新值
      editor.setValue(newValue)

      // 恢复光标位置
      if (position) {
        editor.setPosition(position)
        editor.revealPositionInCenter(position)
      }
    }
  }
)

// 当 props.language 变化时更新编辑器语言
watch(
  () => props.language,
  (newLanguage) => {
    if (editor) {
      monaco.editor.setModelLanguage(editor.getModel(), newLanguage)
    }
  }
)

// 当 props.options 变化时更新编辑器选项
watch(
  () => props.options,
  (newOptions) => {
    if (editor) {
      editor.updateOptions(newOptions)
    }
  },
  { deep: true }
)

// 当 props.readOnly 变化时更新编辑器只读状态
watch(
  () => props.readOnly,
  (newReadOnly) => {
    if (editor) {
      editor.updateOptions({ readOnly: newReadOnly })
    }
  }
)

// 暴露方法给父组件
defineExpose({
  formatCode,
  setCursorPosition,
  getEditor
})
</script>

<style>
.monaco-editor-wrapper {
  position: relative;
  width: 100%;
}

.monaco-editor-container {
  width: 100%;
  border: 1px solid #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.monaco-editor-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.8);
  z-index: 10;
}
</style>
