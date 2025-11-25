from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="书名")
    author = models.CharField(max_length=100, verbose_name="作者")
    publisher = models.CharField(max_length=100, verbose_name="出版社")
    isbn = models.CharField(max_length=20, unique=True, verbose_name="ISBN")
    stock = models.PositiveIntegerField(default=0, verbose_name="库存数量")
    publication_date = models.DateField(verbose_name="出版日期")

    def __str__(self):
        return self.title

class BorrowRecord(models.Model):
    STATUS_CHOICES = (
        ('borrowed', '借出中'),
        ('returned', '已归还'),
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="所借图书")
    borrower_name = models.CharField(max_length=50, verbose_name="借阅人姓名")
    borrow_date = models.DateField(auto_now_add=True, verbose_name="借阅日期")
    due_date = models.DateField(verbose_name="应还日期")
    return_date = models.DateField(null=True, blank=True, verbose_name="实际归还日期")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='borrowed', verbose_name="状态")

    def __str__(self):
        return f"{self.borrower_name} 借阅了《{self.book.title}》"
# 采购记录模型
class PurchaseRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="采购图书")
    quantity = models.PositiveIntegerField(verbose_name="采购数量")
    purchase_date = models.DateField(auto_now_add=True, verbose_name="采购日期")
    operator_name = models.CharField(max_length=50, default="admin", verbose_name="操作员")

    def __str__(self):
        return f"于 {self.purchase_date} 采购《{self.book.title}》{self.quantity}本"
    
class DisposalRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="淘汰图书")
    quantity = models.PositiveIntegerField(verbose_name="淘汰数量")
    disposal_date = models.DateField(auto_now_add=True, verbose_name="淘汰日期")
    reason = models.TextField(blank=True, null=True, verbose_name="淘汰原因")
    operator_name = models.CharField(max_length=50, default="admin", verbose_name="操作员")

    def __str__(self):
        return f"于 {self.disposal_date} 淘汰《{self.book.title}》{self.quantity}本"