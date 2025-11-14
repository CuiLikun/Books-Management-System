from django.contrib import admin
from .models import Book, BorrowRecord,PurchaseRecord,DisposalRecord 

admin.site.register(Book)
admin.site.register(BorrowRecord)
admin.site.register(PurchaseRecord)
admin.site.register(DisposalRecord) # <-- 重点检查这一行