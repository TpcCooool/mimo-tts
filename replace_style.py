import re

with open('src/App.vue', 'r', encoding='utf-8') as f:
    content = f.read()

new_style = """<style scoped>
/* ========================================
   顶部导航栏 (Neo-Brutalism)
   ======================================== */
.header {
  background: var(--accent-1);
  border-bottom: var(--border-width) solid var(--border);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0px 4px 0px var(--shadow-color);
  margin-bottom: 12px;
}
.header-title {
  font-size: 24px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: -0.5px;
}
.header-badge {
  background: var(--accent-2);
  color: var(--text);
  font-size: 12px;
  padding: 4px 10px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  font-weight: 700;
  box-shadow: 2px 2px 0px var(--shadow-color);
}
.header-subtitle {
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
}

/* ========================================
   主容器
   ======================================== */
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ========================================
   卡片
   ======================================== */
.card {
  background: var(--card);
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
  transform: translate(-2px, -2px);
  box-shadow: 8px 8px 0px var(--shadow-color);
}
.card-title {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  text-transform: uppercase;
  border-bottom: 2px solid var(--border);
  padding-bottom: 8px;
}
.card-center {
  text-align: center;
}
.card-help {
  font-size: 14px;
  font-weight: 500;
  background: var(--accent-3);
  color: #000;
}

/* ========================================
   模型选择网格
   ======================================== */
.model-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.model-option {
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
  background: #fff;
  box-shadow: var(--shadow-hover);
}
.model-option:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow);
}
.model-option.active {
  background: var(--accent-1);
  transform: translate(2px, 2px);
  box-shadow: 0px 0px 0px var(--shadow-color);
}
.model-name {
  font-size: 16px;
  font-weight: 800;
  margin-bottom: 6px;
  text-transform: uppercase;
}
.model-id {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: monospace;
  font-weight: 700;
  margin-bottom: 10px;
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  display: inline-block;
  border: 1px solid var(--border);
}
.model-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  font-weight: 500;
}
.model-check {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 28px;
  height: 28px;
  border: 2px solid var(--border);
  border-radius: 0;
  background: var(--accent-2);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 800;
  box-shadow: 2px 2px 0px var(--shadow-color);
}

/* ========================================
   表单控件
   ======================================== */
label {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  text-transform: uppercase;
}
select,
textarea,
.file-input {
  width: 100%;
  padding: 12px 16px;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 500;
  font-family: inherit;
  background: #fff;
  color: var(--text);
  transition: all 0.2s;
  box-shadow: var(--shadow-hover);
}
select:focus,
textarea:focus,
.file-input:focus {
  outline: none;
  background: #fff;
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow);
}
textarea {
  resize: vertical;
  min-height: 100px;
}
.file-input {
  padding: 10px;
  cursor: pointer;
  background: var(--accent-1);
}
.required {
  color: var(--primary);
  font-weight: 900;
  font-size: 18px;
}
.hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
  line-height: 1.5;
  font-weight: 500;
}
.hint code {
  background: var(--accent-1);
  padding: 2px 6px;
  border: 1px solid var(--border);
  border-radius: 0;
  font-size: 12px;
  font-weight: 700;
  color: #000;
}
.form-group {
  margin-bottom: 20px;
}
.form-group:last-child {
  margin-bottom: 0;
}
.section-divider {
  margin-top: 24px;
  padding-top: 20px;
  border-top: var(--border-width) dashed var(--border);
}

/* ========================================
   按钮
   ======================================== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 36px;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 800;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.1s;
  font-family: inherit;
  box-shadow: var(--shadow);
}
.btn-primary {
  background: var(--primary);
  color: #fff;
  text-shadow: 1px 1px 0px #000;
}
.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translate(2px, 2px);
  box-shadow: var(--shadow-hover);
}
.btn-primary:active:not(:disabled) {
  transform: translate(6px, 6px);
  box-shadow: var(--shadow-active);
}
.btn-primary:disabled {
  background: #ccc;
  color: #666;
  text-shadow: none;
  cursor: not-allowed;
  box-shadow: none;
  transform: translate(6px, 6px);
}

/* ========================================
   加载动画
   ======================================== */
.spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 3px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ========================================
   错误信息
   ======================================== */
.error-msg {
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  margin-top: 16px;
  padding: 12px 16px;
  background: var(--primary);
  border: var(--border-width) solid var(--border);
  box-shadow: 4px 4px 0px var(--border);
}

/* ========================================
   音频播放器
   ======================================== */
.audio-player {
  margin-top: 24px;
  padding: 20px;
  background: var(--accent-1);
  border: var(--border-width) solid var(--border);
  box-shadow: var(--shadow-hover);
}
.audio-label {
  font-size: 15px;
  font-weight: 800;
  color: #000;
  margin-bottom: 12px;
  text-transform: uppercase;
}
.audio-player audio {
  width: 100%;
  border: 2px solid var(--border);
  border-radius: 0;
  background: #fff;
}
.audio-player audio::-webkit-media-controls-panel {
  background: #fff;
  border-radius: 0;
}
.download-btns {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  justify-content: center;
}
.btn-download {
  padding: 10px 24px;
  font-size: 14px;
  background: #fff;
  color: #000;
  border: var(--border-width) solid var(--border);
  box-shadow: 3px 3px 0px var(--border);
  font-weight: 800;
  text-transform: uppercase;
}
.btn-download:hover:not(:disabled) {
  background: var(--accent-2);
  transform: translate(2px, 2px);
  box-shadow: 1px 1px 0px var(--border);
}
.btn-download:active:not(:disabled) {
  transform: translate(3px, 3px);
  box-shadow: 0px 0px 0px var(--border);
}
.btn-download:disabled {
  background: #eee;
  color: #999;
  cursor: not-allowed;
  box-shadow: none;
  transform: translate(3px, 3px);
}

/* ========================================
   帮助列表
   ======================================== */
.help-list {
  padding-left: 24px;
}
.help-list li {
  margin-bottom: 8px;
}
.help-list code {
  background: #fff;
  padding: 2px 6px;
  border: 1px solid var(--border);
  border-radius: 0;
  font-size: 13px;
  font-weight: 700;
  color: #000;
}
.help-list a {
  color: var(--primary);
  font-weight: 800;
  text-decoration: none;
  border-bottom: 2px solid var(--primary);
}
.help-list a:hover {
  background: var(--primary);
  color: #fff;
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 640px) {
  .model-grid {
    grid-template-columns: 1fr;
  }
}
</style>"""

new_content = re.sub(r'<style scoped>.*</style>', new_style, content, flags=re.DOTALL)

with open('src/App.vue', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Style replacement completed.")
