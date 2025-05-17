<template>
  <div ref="editorContainer" class="monaco-editor-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
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
  }
})

const emit = defineEmits(['update:value'])

const editorContainer = ref(null)
let editor = null

onMounted(() => {
  // Ensure Monaco workers are initialized
  initMonacoWorkers()

  // Use setTimeout to ensure the DOM is fully rendered
  setTimeout(() => {
    if (editorContainer.value) {
      editor = monaco.editor.create(editorContainer.value, {
        value: props.value,
        language: props.language,
        theme: 'vs',
        automaticLayout: true,
        scrollBeyondLastLine: false,
        minimap: { enabled: false },
        ...props.options
      })

      // Listen for changes
      editor.onDidChangeModelContent(() => {
        const value = editor.getValue()
        emit('update:value', value)
      })

      // Handle window resize
      window.addEventListener('resize', () => {
        if (editor) {
          editor.layout()
        }
      })
    }
  }, 100)
})

onBeforeUnmount(() => {
  // Remove event listener
  window.removeEventListener('resize', () => {
    if (editor) {
      editor.layout()
    }
  })

  // Dispose editor
  if (editor) {
    editor.dispose()
    editor = null
  }
})

// Update editor value when prop changes
watch(
  () => props.value,
  (newValue) => {
    if (editor && newValue !== editor.getValue()) {
      editor.setValue(newValue)
    }
  }
)

// Update editor language when prop changes
watch(
  () => props.language,
  (newLanguage) => {
    if (editor) {
      monaco.editor.setModelLanguage(editor.getModel(), newLanguage)
    }
  }
)

// Update editor options when prop changes
watch(
  () => props.options,
  (newOptions) => {
    if (editor) {
      editor.updateOptions(newOptions)
    }
  },
  { deep: true }
)
</script>

<style>
.monaco-editor-container {
  width: 100%;
  height: 400px;
  border: 1px solid #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}
</style>
