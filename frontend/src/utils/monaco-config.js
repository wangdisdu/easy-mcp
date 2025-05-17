/**
 * Monaco Editor configuration
 * This file configures Monaco Editor's web workers
 */

import * as monaco from 'monaco-editor'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker'
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker'
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'

/**
 * Initialize Monaco Editor's web workers
 */
export function initMonacoWorkers() {
  // Set global MonacoEnvironment
  window.MonacoEnvironment = {
    getWorker(_, label) {
      if (label === 'json') {
        return new jsonWorker()
      }
      if (label === 'css' || label === 'scss' || label === 'less') {
        return new cssWorker()
      }
      if (label === 'html' || label === 'handlebars' || label === 'razor') {
        return new htmlWorker()
      }
      if (label === 'typescript' || label === 'javascript') {
        return new tsWorker()
      }
      return new editorWorker()
    }
  }
}

/**
 * Configure Monaco Editor
 */
export function configureMonaco() {
  // Initialize web workers
  initMonacoWorkers()

  // Configure editor defaults
  monaco.editor.defineTheme('easymcp-theme', {
    base: 'vs',
    inherit: true,
    rules: [],
    colors: {
      'editor.background': '#ffffff',
      'editor.lineHighlightBackground': '#f5f5f5',
      'editorLineNumber.foreground': '#999999',
      'editor.selectionBackground': '#b3d4fc'
    }
  })

  // Set as default theme
  monaco.editor.setTheme('easymcp-theme')

  // Configure editor defaults
  monaco.editor.EditorOptions.lineNumbers.defaultValue = 'on'
  monaco.editor.EditorOptions.scrollBeyondLastLine.defaultValue = false
  monaco.editor.EditorOptions.minimap.defaultValue = { enabled: false }
  monaco.editor.EditorOptions.scrollbar.defaultValue = { alwaysConsumeMouseWheel: false }
}
