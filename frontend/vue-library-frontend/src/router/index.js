import { createRouter, createWebHistory } from 'vue-router'
import BookManagement from '../views/BookManagement.vue'
import Dashboard from '../views/Dashboard.vue' // 确保你的Dashboard.vue还在
import BorrowHistory from '../views/BorrowHistory.vue'

import PurchaseHistory from '../views/PurchaseHistory.vue'
import DisposalHistory from '../views/DisposalHistory.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/books', // 重定向根路径到图书管理页
    },
    {
      path: '/books',
      name: 'book-management',
      component: BookManagement,
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: Dashboard,
    },
    {
      path: '/history',
      name: 'borrow-history',
      component: BorrowHistory,
    },
    {
      path: '/history/purchase',
      name: 'purchase-history',
      component: PurchaseHistory,
    },
    {
      path: '/history/disposal',
      name: 'disposal-history',
      component: DisposalHistory,
    },
  ],
})

export default router
