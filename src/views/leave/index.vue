<template>
  <el-card shadow="never" class="leave-card">
    <h3>请假申请</h3>
    <el-form :model="leaveForm" label-width="80px">
      <el-form-item label="姓名">
        <el-input v-model="leaveForm.name" placeholder="请输入姓名"></el-input>
      </el-form-item>
      <el-form-item label="请假类型">
        <el-select v-model="leaveForm.type" placeholder="请选择">
          <el-option label="事假" value="事假"></el-option>
          <el-option label="病假" value="病假"></el-option>
          <el-option label="年假" value="年假"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="开始时间">
        <el-date-picker v-model="leaveForm.startTime" type="date" placeholder="选择日期"></el-date-picker>
      </el-form-item>
      <el-form-item label="结束时间">
        <el-date-picker v-model="leaveForm.endTime" type="date" placeholder="选择日期"></el-date-picker>
      </el-form-item>
      <el-form-item label="请假原因">
        <el-input v-model="leaveForm.reason" type="textarea" rows="4" placeholder="填写请假原因"></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submitForm">提交申请</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
const leaveForm = ref({
  name: '',
  type: '',
  startTime: '',
  endTime: '',
  reason: ''
})

const submitForm = () => {
  alert('提交成功！')
  console.log(leaveForm.value)
}
const resetForm = () => {
  leaveForm.value = {
    name: '',
    type: '',
    startTime: '',
    endTime: '',
    reason: ''
  }
}
</script>

<style scoped>
.leave-card {
  width: 600px;
  margin: 30px auto;
}
</style>
