# books/urls.py
from django.urls import path
from .views import (
    BookListCreateAPIView, 
    BookDetailAPIView, 
    StatisticsAPIView,
    PurchaseBookAPIView,
    DisposalBookAPIView,
     BorrowBookAPIView,
     BorrowRecordListView,
    ReturnBookAPIView,
    PurchaseRecordListView,
    DisposalRecordListView
)

urlpatterns = [
    path('books/', BookListCreateAPIView.as_view(), name='book-list-create'),
    path('books/<int:pk>/', BookDetailAPIView.as_view(), name='book-detail'),
    path('statistics/', StatisticsAPIView.as_view(), name='statistics'), # 【新增这条URL】
    path('books/<int:pk>/purchase/', PurchaseBookAPIView.as_view(), name='book-purchase'),
     path('books/<int:pk>/disposal/', DisposalBookAPIView.as_view(), name='book-disposal'),
     path('books/<int:pk>/borrow/', BorrowBookAPIView.as_view(), name='book-borrow'),
      path('borrow-records/', BorrowRecordListView.as_view(), name='borrow-record-list'),
    path('borrow-records/<int:pk>/return/', ReturnBookAPIView.as_view(), name='borrow-record-return'),
     path('purchase-records/', PurchaseRecordListView.as_view(), name='purchase-record-list'),
     path('disposal-records/', DisposalRecordListView.as_view(), name='disposal-record-list'),
]