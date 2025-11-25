from rest_framework import serializers
from .models import Book, BorrowRecord, PurchaseRecord, DisposalRecord

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__' # 包含所有字段


class BookTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title']

class BorrowRecordSerializer(serializers.ModelSerializer):
    # 使用上面的 BookTitleSerializer 来显示关联图书的标题
    book = BookTitleSerializer(read_only=True)
    
    class Meta:
        model = BorrowRecord
        fields = '__all__' # 包含所有字段

class PurchaseRecordSerializer(serializers.ModelSerializer):
    # 同样，使用嵌套Serializer来显示书名而不是ID
    book = BookTitleSerializer(read_only=True)

    class Meta:
        model = PurchaseRecord
        fields = '__all__'

class DisposalRecordSerializer(serializers.ModelSerializer):
    book = BookTitleSerializer(read_only=True)

    class Meta:
        model = DisposalRecord
        fields = '__all__'