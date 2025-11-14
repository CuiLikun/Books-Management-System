<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import {
  ElButton,
  ElTable,
  ElTableColumn,
  ElMessage,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElDatePicker,
  ElMessageBox,
} from 'element-plus'

// --- Data Refs ---
const tableData = ref([])
const searchQuery = ref('')

// 新增/编辑功能的 refs
const dialogVisible = ref(false)
const formMode = ref('add')
const bookFormRef = ref(null)
const bookForm = ref({
  id: null,
  title: '',
  author: '',
  publisher: '',
  isbn: '',
  stock: 1,
  publication_date: '',
})

// 采购/淘汰/借阅等业务功能的 refs
const actionDialogVisible = ref(false)
const actionType = ref('purchase')
const currentBook = ref(null)
const actionForm = ref({
  quantity: 1,
  reason: '',
  borrower_name: '',
  due_date: '',
})

// --- Computed Properties ---
const dialogTitle = computed(() => {
  return formMode.value === 'add' ? '新增图书' : '编辑图书'
})

const actionDialogTitle = computed(() => {
  if (!currentBook.value) return ''
  if (actionType.value === 'purchase') {
    return `采购入库 - 《${currentBook.value.title}》`
  }
  if (actionType.value === 'disposal') {
    return `淘汰出库 - 《${currentBook.value.title}》`
  }
  if (actionType.value === 'borrow') {
    return `借阅图书 - 《${currentBook.value.title}》`
  }
  return '业务操作'
})

// --- API Functions ---
const API_URL = 'http://127.0.0.1:8000/api/books/'

const fetchBooks = async () => {
  try {
    const response = await axios.get(API_URL, {
      params: { search: searchQuery.value },
    })
    tableData.value = response.data
  } catch (error) {
    console.error('获取图书列表失败:', error)
    ElMessage.error('数据加载失败！')
  }
}

// --- Event Handlers ---
const handleSearch = () => {
  fetchBooks()
}
const handleAdd = () => {
  formMode.value = 'add'
  bookForm.value = {
    id: null,
    title: '',
    author: '',
    publisher: '',
    isbn: '',
    stock: 1,
    publication_date: '',
  }
  dialogVisible.value = true
}
const handleEdit = (row) => {
  formMode.value = 'edit'
  bookForm.value = Object.assign({}, row)
  dialogVisible.value = true
}
const submitForm = async () => {
  try {
    if (formMode.value === 'add') {
      await axios.post(API_URL, bookForm.value)
      ElMessage.success('新增图书成功！')
    } else {
      await axios.put(`${API_URL}${bookForm.value.id}/`, bookForm.value)
      ElMessage.success('更新图书成功！')
    }
    dialogVisible.value = false
    await fetchBooks()
  } catch (error) {
    const action = formMode.value === 'add' ? '新增' : '更新'
    ElMessage.error(`${action}图书失败，请检查ISBN是否重复！`)
  }
}
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`您确定要删除《${row.title}》这本书吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await axios.delete(`${API_URL}${row.id}/`)
    ElMessage.success('删除成功！')
    await fetchBooks()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败！')
  }
}
const handlePurchase = (bookRow) => {
  currentBook.value = bookRow
  actionType.value = 'purchase'
  actionForm.value.quantity = 1
  actionDialogVisible.value = true
}
const handleDisposal = (bookRow) => {
  currentBook.value = bookRow
  actionType.value = 'disposal'
  actionForm.value.quantity = 1
  actionForm.value.reason = ''
  actionDialogVisible.value = true
}
const handleBorrow = (bookRow) => {
  currentBook.value = bookRow
  actionType.value = 'borrow'
  actionForm.value.borrower_name = ''
  actionForm.value.due_date = ''
  actionDialogVisible.value = true
}
const submitActionForm = async () => {
  if (!currentBook.value) return
  try {
    const bookId = currentBook.value.id
    let url = ''
    let successMessage = ''
    let payload = {}

    if (actionType.value === 'purchase' || actionType.value === 'disposal') {
      url = `${API_URL}${bookId}/${actionType.value}/`
      successMessage = actionType.value === 'purchase' ? '入库成功！' : '出库成功！'
      payload = {
        quantity: actionForm.value.quantity,
        reason: actionForm.value.reason,
      }
    } else if (actionType.value === 'borrow') {
      url = `${API_URL}${bookId}/borrow/`
      successMessage = '借阅成功！'
      payload = {
        borrower_name: actionForm.value.borrower_name,
        due_date: actionForm.value.due_date,
      }
    }

    if (!url) return
    await axios.post(url, payload)

    ElMessage.success(successMessage)
    actionDialogVisible.value = false
    await fetchBooks()
  } catch (error) {
    const errorMessage = error.response?.data?.error || '操作失败！'
    ElMessage.error(errorMessage)
    console.error('操作失败:', error)
  }
}

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchBooks()
})
</script>

<template>
  <div>
    <!-- 操作栏 -->
    <div class="actions-bar" style="margin-bottom: 20px; display: flex; align-items: center">
      <el-button type="primary" @click="handleAdd">新增图书</el-button>
      <div class="search-bar" style="margin-left: 20px; display: flex">
        <el-input
          v-model="searchQuery"
          placeholder="按书名、作者、ISBN搜索"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          style="width: 300px"
        />
        <el-button type="primary" @click="handleSearch" style="margin-left: 10px">搜索</el-button>
      </div>
    </div>

    <!-- 图书列表表格 -->
    <el-table :data="tableData" border style="width: 100%">
      <!-- 使用表格内置索引列，基于当前数据顺序显示行号，删除后会自动重排 -->
      <el-table-column type="index" label="ID" width="60" />
      <el-table-column prop="title" label="书名" />
      <el-table-column prop="author" label="作者" />
      <el-table-column prop="publisher" label="出版社" />
      <el-table-column prop="isbn" label="ISBN" />
      <el-table-column prop="stock" label="库存" />
      <el-table-column prop="publication_date" label="出版日期" />
      <el-table-column label="操作" width="310">
        <template #default="scope">
          <div class="action-buttons">
            <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
            <el-button type="success" size="small" @click="handlePurchase(scope.row)"
              >入库</el-button
            >
            <el-button type="warning" size="small" @click="handleDisposal(scope.row)"
              >出库</el-button
            >
            <template v-if="scope.row.stock > 0">
              <el-button type="primary" size="small" @click="handleBorrow(scope.row)"
                >借阅</el-button
              >
            </template>
            <template v-else>
              <el-button type="info" size="small" disabled>无库存</el-button>
            </template>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑 对话框 -->
    <el-dialog
      :model-value="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @update:modelValue="dialogVisible = $event"
    >
      <el-form :model="bookForm" ref="bookFormRef" label-width="80px">
        <el-form-item label="书名" prop="title"><el-input v-model="bookForm.title" /></el-form-item>
        <el-form-item label="作者" prop="author"
          ><el-input v-model="bookForm.author"
        /></el-form-item>
        <el-form-item label="出版社" prop="publisher"
          ><el-input v-model="bookForm.publisher"
        /></el-form-item>
        <el-form-item label="ISBN" prop="isbn"><el-input v-model="bookForm.isbn" /></el-form-item>
        <el-form-item label="库存" prop="stock"
          ><el-input-number v-model="bookForm.stock" :min="0"
        /></el-form-item>
        <el-form-item label="出版日期" prop="publication_date">
          <el-date-picker
            v-model="bookForm.publication_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 采购/淘汰/借阅等业务操作 对话框 -->
    <el-dialog
      :model-value="actionDialogVisible"
      :title="actionDialogTitle"
      width="400px"
      @update:modelValue="actionDialogVisible = $event"
    >
      <el-form
        v-if="actionType === 'purchase' || actionType === 'disposal'"
        :model="actionForm"
        label-width="80px"
      >
        <el-form-item label="操作数量" prop="quantity">
          <el-input-number v-model="actionForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item v-if="actionType === 'disposal'" label="淘汰原因" prop="reason">
          <el-input
            v-model="actionForm.reason"
            type="textarea"
            :rows="2"
            placeholder="请输入淘汰原因"
          />
        </el-form-item>
      </el-form>
      <el-form v-else-if="actionType === 'borrow'" :model="actionForm" label-width="80px">
        <el-form-item label="借阅人" prop="borrower_name">
          <el-input v-model="actionForm.borrower_name" placeholder="请输入借阅人姓名" />
        </el-form-item>
        <el-form-item label="应还日期" prop="due_date">
          <el-date-picker
            v-model="actionForm.due_date"
            type="date"
            placeholder="请选择应还日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="actionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitActionForm">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<!-- 新增：用于操作按钮的布局样式 -->
<style scoped>
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.action-buttons .el-button {
  padding: 6px 10px;
  font-size: 12px;
}
/* 窄屏时按钮换行，每行最多两个按钮，保证表格宽度不溢出 */
@media (max-width: 640px) {
  .action-buttons .el-button {
    flex: 1 1 calc(50% - 8px);
    min-width: 110px;
  }
}
</style>
