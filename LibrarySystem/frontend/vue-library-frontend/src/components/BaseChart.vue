<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';

// 引入 ECharts 核心模块，核心模块提供了 ECharts 使用必须要的接口。
import * as echarts from 'echarts/core';
// 引入柱状图图表，图表后缀都为 Chart
import { BarChart, LineChart, PieChart } from 'echarts/charts';
// 引入提示框，标题，直角坐标系，数据集，内置数据转换器组件。
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  LegendComponent,
} from 'echarts/components';
// 标签自动布局，全局过渡动画等特性
import { LabelLayout, UniversalTransition } from 'echarts/features';
// 引入 Canvas 渲染器，注意引入 CanvasRenderer 或者 SVGRenderer 是必须的一步
import { CanvasRenderer } from 'echarts/renderers';

// 注册必须的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  LegendComponent,
  BarChart,
  LineChart,
  PieChart,
  LabelLayout,
  UniversalTransition,
  CanvasRenderer,
]);

// 定义组件接收的属性
const props = defineProps({
  // 图表的配置项
  option: {
    type: Object,
    required: true,
  },
  // 图表容器的样式
  style: {
    type: Object,
    default: () => ({ width: '100%', height: '400px' }),
  },
});

const chartRef = ref(null); // 图表DOM的引用
let myChart = null; // ECharts 实例

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    myChart = echarts.init(chartRef.value);
    myChart.setOption(props.option);
  }
};

// 窗口大小变化时，自动调整图表大小
const resizeChart = () => {
  if (myChart) {
    myChart.resize();
  }
};

// 组件挂载后执行
onMounted(() => {
  initChart();
  window.addEventListener('resize', resizeChart);
});

// 组件卸载前执行
onUnmounted(() => {
  if (myChart) {
    myChart.dispose(); // 销毁实例，释放资源
  }
  window.removeEventListener('resize', resizeChart);
});

// 监听option的变化，当外部传入新的option时，重新设置图表
watch(() => props.option, (newOption) => {
  if (myChart) {
    myChart.setOption(newOption);
  }
}, { deep: true }); // 使用深度监听

</script>

<template>
  <div ref="chartRef" :style="props.style"></div>
</template>

<style scoped>
/* 你可以在这里添加一些样式 */
</style>