<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElTable, ElTableColumn, ElButton, ElTag, ElMessage, ElMessageBox } from 'element-plus';

const historyData = ref([]);
const API_URL = 'http://127.0.0.1:8000/api/borrow-records/';

// 获取借阅历史
const fetchHistory = async () => {
  try {
    const response = await axios.get(API_URL);
    historyData.value = response.data;
  } catch (error) {
    console.error("获取借阅历史失败:", error);
    ElMessage.error('借阅历史加载失败！');
  }
};

// 处理还书
const handleReturn = async (record) => {
  try {
    await ElMessageBox.confirm(
      `确定要将《${record.book.title}》标记为已归还吗?`,
      '归还确认',
      { type: 'info' }
    );
    
    await axios.post(`${API_URL}${record.id}/return/`);
    ElMessage.success('归还成功！');
    await fetchHistory(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('归还操作失败！');
    }
  }
};

onMounted(() => {
  fetchHistory();
});
</script>

<template>
  <div>
    <h1>借阅历史记录</h1>
    <el-table :data="historyData" border style="width: 100%">
      <el-table-column prop="id" label="记录ID" width="80" />
      <el-table-column prop="book.title" label="书名" />
      <el-table-column prop="borrower_name" label="借阅人" />
      <el-table-column prop="borrow_date" label="借阅日期" />
      <el-table-column prop="due_date" label="应还日期" />
      <el-table-column prop="return_date" label="实际归还日期" />
      <el-table-column label="状态">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 'borrowed'" type="danger">借出中</el-tag>
          <el-tag v-else type="success">已归还</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button
            v-if="scope.row.status === 'borrowed'"
            type="primary"
            size="small"
            @click="handleReturn(scope.row)"
          >
            归还
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>