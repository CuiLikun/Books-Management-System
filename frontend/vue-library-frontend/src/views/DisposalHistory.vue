<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElTable, ElTableColumn, ElMessage } from 'element-plus';

const historyData = ref([]);
const API_URL = 'http://127.0.0.1:8000/api/disposal-records/';

const fetchHistory = async () => {
  try {
    const response = await axios.get(API_URL);
    historyData.value = response.data;
  } catch (error) {
    ElMessage.error('淘汰历史加载失败！');
  }
};

onMounted(() => { fetchHistory(); });
</script>

<template>
  <div>
    <h1>淘汰历史记录</h1>
    <el-table :data="historyData" border style="width: 100%" empty-text="暂无淘汰记录">
      <el-table-column prop="id" label="记录ID" width="80" />
      <el-table-column prop="book.title" label="书名" />
      <el-table-column prop="quantity" label="淘汰数量" />
      <el-table-column prop="reason" label="淘汰原因" />
      <el-table-column prop="disposal_date" label="淘汰日期" sortable />
      <el-table-column prop="operator_name" label="操作员" />
    </el-table>
  </div>
</template>