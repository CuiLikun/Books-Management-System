<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import BaseChart from '@/components/BaseChart.vue'; // 确保BaseChart组件路径正确
import { ElMessage, ElRow, ElCol, ElStatistic } from 'element-plus';

// --- Data Refs ---
// 总览数据
const summaryData = ref({
  total_book_types: 0,
  total_stock: 0,
  current_borrowed_count: 0,
});

// ECharts option objects
const topBorrowedOption = ref({});
const publisherOption = ref({});
const borrowTrendsOption = ref({});

// --- API Function ---
const fetchStatistics = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/statistics/');
    const data = response.data;

    // 1. 更新总览数据
    summaryData.value = data.summary;

    // 2. 配置“借阅排行榜”条形图
    topBorrowedOption.value = {
      title: { text: '热门借阅图书 Top 5' },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'category', data: data.top_5_borrowed.labels, axisLabel: { interval: 0, rotate: 30 } },
      yAxis: { type: 'value' },
      series: [{ name: '借阅次数', type: 'bar', data: data.top_5_borrowed.values }],
      grid: { containLabel: true },
    };

    // 3. 配置“出版社分布”饼图
    publisherOption.value = {
      title: { text: '各出版社图书种类分布', left: 'center' },
      tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', left: 10, data: data.publisher_distribution.map(p => p.name) },
      series: [{
        name: '图书种类',
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: '30', fontWeight: 'bold' } },
        labelLine: { show: false },
        data: data.publisher_distribution,
      }],
    };

    // 4. 配置“借阅趋势”折线图
    borrowTrendsOption.value = {
      title: { text: '每月借阅趋势' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', boundaryGap: false, data: data.borrow_trends.labels },
      yAxis: { type: 'value' },
      series: [{ name: '借阅次数', type: 'line', data: data.borrow_trends.values, areaStyle: {} }],
    };

  } catch (error) {
    console.error("获取统计数据失败:", error);
    ElMessage.error('统计数据加载失败！');
  }
};

// --- Lifecycle Hook ---
onMounted(() => {
  fetchStatistics();
});
</script>

<template>
  <div class="dashboard-page">
    <h1>数据统计面板</h1>

    <!-- 数据总览 -->
    <el-row :gutter="20" class="summary-row">
      <el-col :span="8">
        <el-statistic title="图书总种类" :value="summaryData.total_book_types" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="总库存量" :value="summaryData.total_stock" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="当前借出总数" :value="summaryData.current_borrowed_count" />
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="chart-container">
          <BaseChart :option="topBorrowedOption" :style="{ height: '400px' }" />
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-container">
          <BaseChart :option="publisherOption" :style="{ height: '400px' }" />
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <div class="chart-container">
          <BaseChart :option="borrowTrendsOption" :style="{ height: '400px' }" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard-page {
  padding: 20px;
}
.summary-row {
  margin-bottom: 20px;
}
.el-col {
  text-align: center;
  background-color: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}
.chart-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}
</style>