<template>
  <el-card shadow="never" class="section">
    <el-form
      ref="formRef"
      :model="leaveForm"
      :rules="rules"
      label-width="90px"
      class="leave__form"
      @submit.prevent
    >
      <el-form-item label="申请人">
        <el-input v-model="leaveForm.name" disabled />
      </el-form-item>

      <el-form-item label="请假类型" prop="type">
        <el-select v-model="leaveForm.type" placeholder="请选择" style="width: 100%">
          <el-option label="事假" value="事假" />
          <el-option label="病假" value="病假" />
          <el-option label="年假" value="年假" />
        </el-select>
      </el-form-item>

      <el-form-item label="开始时间" prop="startTime">
        <el-date-picker
          v-model="leaveForm.startTime"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          @change="onStartChange"
        />
      </el-form-item>

      <el-form-item label="结束时间" prop="endTime">
        <el-date-picker
          v-model="leaveForm.endTime"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledEndDate"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item v-if="days > 0" label="合计天数">
        <el-tag type="primary" effect="plain">{{ days }} 天</el-tag>
      </el-form-item>

      <el-form-item label="请假原因" prop="reason">
        <el-input
          v-model="leaveForm.reason"
          type="textarea"
          :rows="4"
          maxlength="200"
          show-word-limit
          placeholder="填写请假原因"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          <el-icon><Check /></el-icon>
          提交申请
        </el-button>
        <el-button @click="resetForm">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
/**
 * 请假申请表单：自带校验和日期联动。
 * 校验通过后把填好的数据抛给父级（emit submit），存到哪由父级决定。
 */
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Refresh } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'

const emit = defineEmits(['submit'])

const { userName } = useUserProfile()
const formRef = ref()
const submitting = ref(false)

const createEmptyForm = () => ({
  name: userName.value,
  type: '',
  startTime: '',
  endTime: '',
  reason: '',
})

const leaveForm = reactive(createEmptyForm())

// 顶栏改了显示名称后，表单里的申请人跟着变
watch(userName, (name) => {
  leaveForm.name = name
})

/** 结束时间不能早于开始时间 */
function validateEndTime(rule, value, callback) {
  if (!value || !leaveForm.startTime) return callback()
  if (value < leaveForm.startTime) {
    callback(new Error('结束时间不能早于开始时间'))
  } else {
    callback()
  }
}

const rules = {
  type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    { validator: validateEndTime, trigger: 'change' },
  ],
  reason: [
    { required: true, message: '请填写请假原因', trigger: 'blur' },
    { min: 5, max: 200, message: '请假原因 5 - 200 个字', trigger: 'blur' },
  ],
}

/** 转成本地日期字符串（YYYY-MM-DD），避免时区把日期算偏 */
function toDateStr(date) {
  const p = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`
}

/** 开始时间往后调时，清掉已经非法的结束时间 */
function onStartChange() {
  if (leaveForm.endTime && leaveForm.endTime < leaveForm.startTime) {
    leaveForm.endTime = ''
  }
  // validateField 校验不通过时会 reject，这里必须接住，否则控制台报未捕获错误
  // 错误提示由表单自己渲染，所以直接忽略即可
  formRef.value?.validateField('endTime').catch(() => {})
}

/** 结束时间选择器里，禁掉开始时间之前的日期 */
function disabledEndDate(date) {
  return leaveForm.startTime ? toDateStr(date) < leaveForm.startTime : false
}

/** 请假天数（含首尾两天） */
const days = computed(() => {
  if (!leaveForm.startTime || !leaveForm.endTime) return 0
  const diff = new Date(leaveForm.endTime) - new Date(leaveForm.startTime)
  return diff < 0 ? 0 : diff / 86400000 + 1
})

async function submitForm() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  // 模拟网络请求，让 loading 有效果（答辩演示更好看）
  setTimeout(() => {
    emit('submit', {
      name: leaveForm.name,
      type: leaveForm.type,
      startDate: leaveForm.startTime,
      endDate: leaveForm.endTime,
      days: days.value,
      reason: leaveForm.reason,
    })
    submitting.value = false
    resetForm()
    ElMessage.success('提交成功，等待审批')
  }, 400)
}

function resetForm() {
  formRef.value?.resetFields()
  Object.assign(leaveForm, createEmptyForm())
}
</script>

<style scoped>
.section {
  border: none;
}

.leave__form {
  max-width: 560px;
}
</style>
