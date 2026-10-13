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

const TYPES = ['通知', '活动', '制度']

const visible = defineModel({ type: Boolean, default: false })
const emit = defineEmits(['publish'])

const formRef = ref(null)
const form = reactive({ title: '', type: '通知', content: '', top: false })

const rules = {
  title: [{ required: true, message: '标题不能为空', trigger: 'blur' }],
  content: [{ required: true, message: '内容不能为空', trigger: 'blur' }],
}

function reset() {
  form.title = ''
  form.type = '通知'
  form.content = ''
  form.top = false
  formRef.value?.clearValidate()
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
    publishTime: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`,
  })
  visible.value = false
}
</script>
