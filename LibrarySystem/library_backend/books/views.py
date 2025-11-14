# books/views.py
from rest_framework import generics,filters,status
from .serializers import BookSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
# 2. 从 .models 导入 Book 和 PurchaseRecord
from .models import Book, PurchaseRecord,DisposalRecord, BorrowRecord
# 3. 从 .serializers 导入 BookSerializer
from .serializers import BookSerializer
from .serializers import BorrowRecordSerializer
from django.utils import timezone # 导入 timezone
from .serializers import PurchaseRecordSerializer # 导入新的 Serializer
from .models import DisposalRecord
from .serializers import DisposalRecordSerializer
# 1. 确保从 django.db.models 导入了 Sum 和 Count
from django.db.models import Sum, Count
# 2. 导入 TruncMonth 用于按月分组
from django.db.models.functions import TruncMonth

# 这个视图处理列表获取和新建
class BookListCreateAPIView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'author', 'isbn'] # 指定可以按哪些字段进行搜索

# 【新增这个视图】
# 这个视图处理单本书的获取详情、更新和删除
class BookDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

class StatisticsAPIView(APIView):
    """
    提供多维度的数据统计。
    """
    def get(self, request, *args, **kwargs):
        # 1. 核心数据总览
        total_book_types = Book.objects.count()
        total_stock = Book.objects.aggregate(total=Sum('stock'))['total'] or 0
        total_borrowed_count = BorrowRecord.objects.filter(status='borrowed').count()

        # 2. 借阅次数最多的 Top 5 图书 (条形图数据)
        top_5_borrowed_books = BorrowRecord.objects.values('book__title') \
                                    .annotate(borrow_count=Count('id')) \
                                    .order_by('-borrow_count')[:5]

        # 3. 按出版社分布的图书种类 (饼图数据)
        publisher_distribution = Book.objects.values('publisher') \
                                    .annotate(count=Count('id')) \
                                    .order_by('-count')

        # 4. 每月借阅次数趋势 (折线图数据)
        borrow_trends = BorrowRecord.objects \
                            .annotate(month=TruncMonth('borrow_date')) \
                            .values('month') \
                            .annotate(count=Count('id')) \
                            .order_by('month')
        
        # 准备要返回给前端的数据结构
        data = {
            'summary': {
                'total_book_types': total_book_types,
                'total_stock': total_stock,
                'current_borrowed_count': total_borrowed_count,
            },
            'top_5_borrowed': {
                'labels': [item['book__title'] for item in top_5_borrowed_books],
                'values': [item['borrow_count'] for item in top_5_borrowed_books],
            },
            'publisher_distribution': [
                {'name': item['publisher'], 'value': item['count']} for item in publisher_distribution
            ],
            'borrow_trends': {
                # 将日期对象格式化为 'YYYY-MM' 字符串
                'labels': [item['month'].strftime('%Y-%m') for item in borrow_trends],
                'values': [item['count'] for item in borrow_trends],
            }
        }
        
        return Response(data)
# 【新增这个视图类】
class PurchaseBookAPIView(APIView):
    """
    处理单本图书的采购入库操作。
    接收一个 POST 请求，请求体中应包含 {"quantity": 数量}
    """
    def post(self, request, pk, *args, **kwargs):
        # (1) 验证传入的数量
        try:
            quantity = int(request.data.get('quantity'))
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': '数量必须是一个正整数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # (2) 获取要操作的图书对象
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response(
                {'error': '图书不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # (3) 执行核心业务逻辑：更新库存 + 创建记录
        book.stock += quantity
        book.save()
        
        PurchaseRecord.objects.create(
            book=book, 
            quantity=quantity,
            # 如果未来有用户登录，这里可以换成真实用户名
            # operator_name=request.user.username 
        )

        # (4) 返回成功响应，并附上更新后的图书数据
        serializer = BookSerializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# 【新增这个视图类】
class DisposalBookAPIView(APIView):
    """
    处理单本图书的淘汰出库操作
    """
    def post(self, request, pk, *args, **kwargs):
        # 1. 验证数量
        try:
            quantity = int(request.data.get('quantity'))
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': '数量必须是一个正整数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 提取淘汰原因
        reason = request.data.get('reason', '') # 'reason'是可选的

        # 2. 获取图书
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({'error': '图书不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 3. 【核心业务逻辑】
        # (1) 检查库存是否充足
        if book.stock < quantity:
            return Response(
                {'error': f'库存不足！当前库存仅剩 {book.stock} 本'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # (2) 更新库存
        book.stock -= quantity
        book.save()
        
        # (3) 创建淘汰记录
        DisposalRecord.objects.create(
            book=book, 
            quantity=quantity,
            reason=reason
        )

        # 4. 返回成功响应
        serializer = BookSerializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class BorrowBookAPIView(APIView):
    """
    处理图书的借阅操作
    """
    def post(self, request, pk, *args, **kwargs):
        # 1. 验证传入的数据
        borrower_name = request.data.get('borrower_name')
        due_date = request.data.get('due_date')

        if not borrower_name or not due_date:
            return Response(
                {'error': '借阅人姓名和应还日期不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 获取图书
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({'error': '图书不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 3. 【核心业务逻辑】
        # (1) 检查库存是否 > 0
        if book.stock <= 0:
            return Response(
                {'error': '本书已无库存，无法借阅'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # (2) 更新库存
        book.stock -= 1
        book.save()
        
        # (3) 创建借阅记录
        BorrowRecord.objects.create(
            book=book,
            borrower_name=borrower_name,
            due_date=due_date,
            status='borrowed' # 状态为借出中
        )

        # 4. 返回成功响应
        serializer = BookSerializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class BorrowRecordListView(generics.ListAPIView):
    queryset = BorrowRecord.objects.select_related('book').order_by('-borrow_date')
    serializer_class = BorrowRecordSerializer

class ReturnBookAPIView(APIView):
    def post(self, request, pk, *args, **kwargs):
        try:
            # 找到要归还的这条借阅记录
            borrow_record = BorrowRecord.objects.get(pk=pk, status='borrowed')
        except BorrowRecord.DoesNotExist:
            return Response(
                {'error': '该借阅记录不存在或已归还'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 【核心业务逻辑】
        # 1. 更新借阅记录的状态和归还日期
        borrow_record.status = 'returned'
        borrow_record.return_date = timezone.now().date()
        borrow_record.save()
        
        # 2. 对应图书的库存 +1
        book = borrow_record.book
        book.stock += 1
        book.save()

        # 3. 返回成功响应
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    
class PurchaseRecordListView(generics.ListAPIView):
    """
    提供所有采购记录的列表。
    """
    queryset = PurchaseRecord.objects.select_related('book').order_by('-purchase_date')
    serializer_class = PurchaseRecordSerializer

class DisposalRecordListView(generics.ListAPIView):
    """
    提供所有淘汰记录的列表。
    """
    queryset = DisposalRecord.objects.select_related('book').order_by('disposal_date')
    serializer_class = DisposalRecordSerializer