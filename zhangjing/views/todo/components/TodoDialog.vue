<template>
  <el-dialog
    v-model="visible"
    :title="mode === 'create' ? '新建待办' : '编辑待办'"
    width="520px"
    class="todo-dialog"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="84px" @submit.prevent>
      <el-form-item label="任务名称" prop="title">
        <el-input v-model="form.title" maxlength="40" show-word-limit placeholder="填写任务名称" />
      </el-form-item>
      <el-form-item label="任务描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          maxlength="200"
          show-word-limit
          placeholder="补充任务说明"
        />
      </el-form-item>
      <el-form-item label="分类" prop="category">
        <el-select v-model="form.category" placeholder="选择分类" class="full-width">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="优先级" prop="priority">
        <el-select v-model="form.priority" placeholder="选择优先级" class="full-width">
          <el-option label="高" value="高" />
          <el-option label="中" value="中" />
          <el-option label="低" value="低" />
        </el-select>
      </el-form-item>
      <el-form-item label="负责人" prop="assignee">
        <el-select v-model="form.assignee" placeholder="选择负责人" class="full-width">
          <el-option v-for="item in assignees" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="截止日期" prop="dueDate">
        <el-date-picker
          v-model="form.dueDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择截止日期"
          class="full-width"
        />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="form.status" class="full-width">
          <el-option v-for="item in editableStatuses" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 新建 / 编辑待办弹窗：自己管表单和校验。
 * 打开时按 initial 回填（编辑）或清空（新建），校验通过后 emit save。
 */
import { nextTick, reactive, ref, watch } from 'vue'

const props = defineProps({
  /** 'create' 或 'edit'，只影响标题 */
  mode: { type: String, default: 'create' },
  categories: { type: Array, required: true },
  assignees: { type: Array, required: true },
  editableStatuses: { type: Array, required: true },
  /** 编辑时传进来要回填的那条数据，新建时传 null */
  initial: { type: Object, default: null },
})

const emit = defineEmits(['save'])

const visible = defineModel({ type: Boolean, default: false })

const formRef = ref()

const createEmptyForm = () => ({
  title: '',
  description: '',
  category: '',
  priority: '中',
  assignee: props.assignees[0] ?? '',
  dueDate: '',
  status: '待办',
})

const form = reactive(createEmptyForm())

const rules = {
  title: [
    { required: true, message: '请填写任务名称', trigger: 'blur' },
    { min: 2, max: 40, message: '任务名称需为 2 到 40 个字', trigger: 'blur' },
  ],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  assignee: [{ required: true, message: '请选择负责人', trigger: 'change' }],
  dueDate: [{ required: true, message: '请选择截止日期', trigger: 'change' }],
}

// 每次打开都重置一次，避免残留上一次的校验红字
watch(visible, (open) => {
  if (!open) return
  Object.assign(form, props.initial ? { ...props.initial } : createEmptyForm())
  nextTick(() => formRef.value?.clearValidate())
})

async function save() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  emit('save', { ...form })
  visible.value = false
}
</script>

<style scoped>
.full-width {
  width: 100%;
}

.todo-dialog {
  max-width: 92vw;
}
</style>
