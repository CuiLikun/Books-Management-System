<script setup>
import { RouterView, useRouter } from 'vue-router'
import { Document, TrendCharts, Tickets } from '@element-plus/icons-vue'

const router = useRouter()
const handleMenuSelect = (index) => {
  router.push(index)
}
</script>

<template>
  <el-container class="main-layout">
    <el-aside width="200px">
      <h3 class="system-title">图书管理系统</h3>
      <el-menu default-active="/books" class="el-menu-vertical-demo" @select="handleMenuSelect">
        <el-menu-item index="/books">
          <el-icon><Document /></el-icon>
          <span>图书信息管理</span>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><TrendCharts /></el-icon>
          <span>数据统计面板</span>
        </el-menu-item>

        <!-- 【新增下面这个菜单项】 -->
        <el-sub-menu index="/history">
          <template #title>
            <el-icon><IconMenu /></el-icon>
            <span>历史记录查询</span>
          </template>
          <el-menu-item index="/history">借阅历史</el-menu-item>
          <el-menu-item index="/history/purchase">采购历史</el-menu-item>
          <el-menu-item index="/history/disposal">淘汰历史</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-main>
      <RouterView />
    </el-main>
  </el-container>
</template>

<style scoped>
.main-layout,
.el-menu {
  height: 100vh;
}
.system-title {
  text-align: center;
  margin: 20px 0;
  color: #409eff;
}
.el-main {
  background-color: #f4f4f5;
  padding: 20px;
}
</style>
