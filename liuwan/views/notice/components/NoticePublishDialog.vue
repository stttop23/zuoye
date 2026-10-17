<template>
  <el-dialog v-model="visible" title="发布公告" width="620px" @closed="reset">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="60px">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" maxlength="40" show-word-limit placeholder="标题" />
      </el-form-item>
      <el-form-item label="类型" prop="type">
        <el-select v-model="form.type" style="width: 140px">
          <el-option v-for="item in TYPES" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="内容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="6"
          maxlength="500"
          show-word-limit
          resize="none"
          placeholder="正文"
        />
      </el-form-item>
      <el-form-item label="附件">
        <div class="upload">
          <ul v-if="form.attachments.length" class="upload__list">
            <li v-for="file in form.attachments" :key="file.url" class="upload__item">
              <el-icon><Paperclip /></el-icon>
              <span class="upload__name" :title="file.name">{{ file.name }}</span>
              <span class="upload__size">{{ formatFileSize(file.size) }}</span>
              <button
                type="button"
                class="upload__remove"
                aria-label="移除附件"
                @click="removeFile(file.url)"
              >
                <el-icon><Close /></el-icon>
              </button>
            </li>
          </ul>

          <input
            ref="fileInput"
            type="file"
            class="upload__input"
            :accept="ACCEPT"
            @change="onFileChange"
          />
          <div v-if="form.attachments.length < MAX_FILES">
            <el-button :loading="uploading" @click="pickFile">
              <el-icon><Plus /></el-icon>
              {{ uploading ? '上传中…' : '添加附件' }}
            </el-button>
          </div>
        </div>
      </el-form-item>
      <el-form-item label="置顶">
        <el-switch v-model="form.top" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="submit">发布</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 发布公告弹窗。
 *
 * 以前「发布公告」只在页面上弹一句「当前为前端演示版本」—— 管理员点了没有任何反应，
 * 演示走到这里就冷场了。现在是真的往 @/composables/appStore 的公告列表里插一条：
 * 公告页表格、首页「公告数量」和「最新公告」、顶栏通知中心会一起变，闭环就出来了。
 *
 * ⚠️ publishTime 用本机时间拼字符串，别用 toISOString（它按 UTC 算，会差 8 小时）。
 */
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, Paperclip, Plus } from '@element-plus/icons-vue'
import { formatFileSize, uploadAttachment } from '@/api/notice'

const TYPES = ['通知', '活动', '制度']

/** 单个文件上限（后端也拦，这里只是提前告诉用户） */
const MAX_BYTES = 10 * 1024 * 1024
/** 一条公告最多几个附件：超过 3 个详情里会堆成一面墙 */
const MAX_FILES = 3
const ACCEPT =
  '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md,.csv,.zip,.rar,.7z,.png,.jpg,.jpeg,.gif,.webp'

const visible = defineModel({ type: Boolean, default: false })
const emit = defineEmits(['publish'])

const formRef = ref(null)
const fileInput = ref(null)
const form = reactive({ title: '', type: '通知', content: '', top: false, attachments: [] })

const uploading = ref(false)

const rules = {
  title: [{ required: true, message: '标题不能为空', trigger: 'blur' }],
  content: [{ required: true, message: '内容不能为空', trigger: 'blur' }],
}

function reset() {
  form.title = ''
  form.type = '通知'
  form.content = ''
  form.top = false
  form.attachments = []
  uploading.value = false
  formRef.value?.clearValidate()
}

function pickFile() {
  fileInput.value?.click()
}

/** 选完文件就上传；上传成功后后端返回 { name, size, url }，直接进表单 */
async function onFileChange(event) {
  const file = event.target.files?.[0]
  // 清空 value，否则选同一个文件第二次不会触发 change
  event.target.value = ''
  if (!file) return

  if (file.size > MAX_BYTES) {
    ElMessage.warning('文件不能超过 10MB')
    return
  }

  uploading.value = true
  try {
    form.attachments.push(await uploadAttachment(file))
  } catch (error) {
    ElMessage.error(error.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

function removeFile(url) {
  form.attachments = form.attachments.filter((file) => file.url !== url)
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  emit('publish', {
    title: form.title.trim(),
    type: form.type,
    content: form.content.trim(),
    top: form.top,
    attachments: [...form.attachments],
    publishTime: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`,
  })
  visible.value = false
}
</script>

<style scoped>
.upload {
  display: flex;
  width: 100%;
  flex-direction: column;
  gap: 8px;
}

/* 文件选择框藏起来，点击「添加附件」按钮时代为触发 */
.upload__input {
  display: none;
}

.upload__list {
  display: flex;
  margin: 0;
  padding: 0;
  flex-direction: column;
  gap: 6px;
  list-style: none;
}

.upload__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  color: var(--st-text-regular);
  font-size: 13px;
  background: var(--st-bg-sunken);
  border-radius: var(--st-radius-sm);
}

.upload__name {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload__size {
  flex: 0 0 auto;
  color: var(--st-text-secondary);
  font-size: 12px;
}

.upload__remove {
  display: inline-flex;
  padding: 2px;
  color: var(--st-text-secondary);
  cursor: pointer;
  background: transparent;
  border: 0;
  border-radius: 4px;
}

.upload__remove:hover {
  color: var(--st-danger);
  background: var(--st-danger-light);
}
</style>
