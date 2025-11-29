# library_backend/books/views.py

from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BookSerializer, BorrowRecordSerializer, PurchaseRecordSerializer, DisposalRecordSerializer


# 这是一个非常重要的辅助函数，用于将数据库游标返回的结果转换成Python字典列表
# 这样我们才能将结果传递给Serializer
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# --- 核心CRUD视图 ---


class BookListCreateAPIView(APIView):
    def get(self, request, *args, **kwargs):
        """获取图书列表 (原生SQL SELECT)"""
        search_query = request.query_params.get("search", None)
        sql = "SELECT * FROM books_book"
        params = []
        if search_query:
            sql += " WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s"
            search_term = f"%{search_query}%"
            params = [search_term, search_term, search_term]

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            books = dictfetchall(cursor)

        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """创建新书 (原生SQL INSERT)"""
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            sql = """
                INSERT INTO books_book (title, author, publisher, isbn, stock, publication_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = [
                data["title"],
                data["author"],
                data["publisher"],
                data["isbn"],
                data["stock"],
                data["publication_date"],
            ]
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailAPIView(APIView):
    def get(self, request, pk, *args, **kwargs):
        """获取单本图书详情 (原生SQL SELECT)"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books_book WHERE id = %s", [pk])
            book = dictfetchall(cursor)
        if not book:
            return Response({"error": "图书不存在"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book[0])
        return Response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        """更新图书 (原生SQL UPDATE)"""
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            sql = """
                UPDATE books_book SET
                title=%s, author=%s, publisher=%s, isbn=%s, stock=%s, publication_date=%s
                WHERE id = %s
            """
            params = [
                data["title"],
                data["author"],
                data["publisher"],
                data["isbn"],
                data["stock"],
                data["publication_date"],
                pk,
            ]
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """删除图书 (原生SQL 级联删除)"""
        with connection.cursor() as cursor:
            # 开启事务
            cursor.execute("START TRANSACTION")
            try:
                # --- 关键步骤：先删除所有关联的子记录 ---

                # 1. 删除关联的【采购记录】
                cursor.execute("DELETE FROM books_purchaserecord WHERE book_id = %s", [pk])

                # 2. 删除关联的【借阅记录】
                cursor.execute("DELETE FROM books_borrowrecord WHERE book_id = %s", [pk])

                # 3. 删除关联的【淘汰记录】
                cursor.execute("DELETE FROM books_disposalrecord WHERE book_id = %s", [pk])

                # --- 最后步骤：删除图书本身 ---

                # 4. 删除图书
                rows_affected = cursor.execute("DELETE FROM books_book WHERE id = %s", [pk])

                # 5. 提交事务 (这一步如果不写，删除不会生效)
                cursor.execute("COMMIT")

            except Exception as e:
                # 发生错误回滚
                cursor.execute("ROLLBACK")
                print(f"删除失败原因: {str(e)}")  # 在后台打印错误日志方便调试
                return Response({"error": f"删除失败: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if rows_affected == 0:
            return Response({"error": "图书不存在，无法删除"}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)


# --- 业务操作视图 ---


class PurchaseBookAPIView(APIView):
    """采购入库 (原生SQL UPDATE + INSERT)"""

    def post(self, request, pk, *args, **kwargs):
        try:
            quantity = int(request.data.get("quantity"))
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "数量必须是正整数"}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            # 使用事务确保两步操作要么都成功，要么都失败
            cursor.execute("START TRANSACTION")
            try:
                # 1. 更新库存
                update_sql = "UPDATE books_book SET stock = stock + %s WHERE id = %s"
                updated_rows = cursor.execute(update_sql, [quantity, pk])
                if updated_rows == 0:
                    raise Exception("Book not found")

                # 2. 创建采购记录
                insert_sql = "INSERT INTO books_purchaserecord (book_id, quantity, purchase_date, operator_name) VALUES (%s, %s, CURDATE(), %s)"
                cursor.execute(insert_sql, [pk, quantity, "admin"])

                cursor.execute("COMMIT")
            except Exception as e:
                cursor.execute("ROLLBACK")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # 返回更新后的图书信息
            cursor.execute("SELECT * FROM books_book WHERE id = %s", [pk])
            book = dictfetchall(cursor)
        serializer = BookSerializer(book[0])
        return Response(serializer.data, status=status.HTTP_200_OK)


class DisposalBookAPIView(APIView):
    """淘汰出库 (原生SQL SELECT + UPDATE + INSERT)"""

    def post(self, request, pk, *args, **kwargs):
        # ... (验证quantity和reason的逻辑与之前相同) ...
        quantity = int(request.data.get("quantity"))
        reason = request.data.get("reason", "")

        with connection.cursor() as cursor:
            cursor.execute("START TRANSACTION")
            try:
                # 1. 先检查库存是否充足
                cursor.execute("SELECT stock FROM books_book WHERE id = %s FOR UPDATE", [pk])
                current_stock = cursor.fetchone()
                if not current_stock or current_stock[0] < quantity:
                    raise Exception(f"库存不足！当前库存仅剩 {current_stock[0] if current_stock else 0} 本")

                # 2. 更新库存
                cursor.execute("UPDATE books_book SET stock = stock - %s WHERE id = %s", [quantity, pk])

                # 3. 创建淘汰记录
                cursor.execute(
                    "INSERT INTO books_disposalrecord (book_id, quantity, reason, disposal_date, operator_name) VALUES (%s, %s, %s, CURDATE(), %s)",
                    [pk, quantity, reason, "admin"],
                )

                cursor.execute("COMMIT")
            except Exception as e:
                cursor.execute("ROLLBACK")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            cursor.execute("SELECT * FROM books_book WHERE id = %s", [pk])
            book = dictfetchall(cursor)
        serializer = BookSerializer(book[0])
        return Response(serializer.data, status=status.HTTP_200_OK)


class BorrowBookAPIView(APIView):
    """借阅图书 (原生SQL SELECT + UPDATE + INSERT)"""

    def post(self, request, pk, *args, **kwargs):
        # ... (验证 borrower_name 和 due_date 的逻辑与之前相同) ...
        borrower_name = request.data.get("borrower_name")
        due_date = request.data.get("due_date")

        with connection.cursor() as cursor:
            cursor.execute("START TRANSACTION")
            try:
                # 1. 检查库存
                cursor.execute("SELECT stock FROM books_book WHERE id = %s FOR UPDATE", [pk])
                current_stock = cursor.fetchone()
                if not current_stock or current_stock[0] <= 0:
                    raise Exception("本书已无库存，无法借阅")

                # 2. 更新库存
                cursor.execute("UPDATE books_book SET stock = stock - 1 WHERE id = %s", [pk])

                # 3. 创建借阅记录
                sql = "INSERT INTO books_borrowrecord (book_id, borrower_name, borrow_date, due_date, status) VALUES (%s, %s, CURDATE(), %s, %s)"
                cursor.execute(sql, [pk, borrower_name, due_date, "borrowed"])

                cursor.execute("COMMIT")
            except Exception as e:
                cursor.execute("ROLLBACK")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            cursor.execute("SELECT * FROM books_book WHERE id = %s", [pk])
            book = dictfetchall(cursor)
        serializer = BookSerializer(book[0])
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReturnBookAPIView(APIView):
    """归还图书 (原生SQL UPDATE + UPDATE)"""

    def post(self, request, pk, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("START TRANSACTION")
            try:
                # 1. 获取要归还的记录及其关联的book_id
                sql = "SELECT book_id FROM books_borrowrecord WHERE id = %s AND status = 'borrowed' FOR UPDATE"
                cursor.execute(sql, [pk])
                record = cursor.fetchone()
                if not record:
                    raise Exception("该借阅记录不存在或已归还")

                book_id = record[0]

                # 2. 更新借阅记录
                update_record_sql = (
                    "UPDATE books_borrowrecord SET status = 'returned', return_date = CURDATE() WHERE id = %s"
                )
                cursor.execute(update_record_sql, [pk])

                # 3. 对应图书库存+1
                update_book_sql = "UPDATE books_book SET stock = stock + 1 WHERE id = %s"
                cursor.execute(update_book_sql, [book_id])

                cursor.execute("COMMIT")
            except Exception as e:
                cursor.execute("ROLLBACK")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "success"}, status=status.HTTP_200_OK)


# --- 历史记录查询视图 (SELECT) ---


class BorrowRecordListView(APIView):
    def get(self, request, *args, **kwargs):
        # SQL JOIN 查询来同时获取图书标题
        sql = """
            SELECT br.*, b.title as book_title
            FROM books_borrowrecord br
            JOIN books_book b ON br.book_id = b.id
            ORDER BY br.borrow_date DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            records = dictfetchall(cursor)

        # 为了适配前端期望的 { book: { title: '...' } } 格式，需要手动处理一下
        for record in records:
            record["book"] = {"title": record.pop("book_title")}

        serializer = BorrowRecordSerializer(records, many=True)
        return Response(serializer.data)


class PurchaseRecordListView(APIView):
    def get(self, request, *args, **kwargs):
        sql = """
            SELECT pr.*, b.title as book_title
            FROM books_purchaserecord pr
            JOIN books_book b ON pr.book_id = b.id
            ORDER BY pr.purchase_date DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            records = dictfetchall(cursor)

        for record in records:
            record["book"] = {"title": record.pop("book_title")}

        serializer = PurchaseRecordSerializer(records, many=True)
        return Response(serializer.data)


class DisposalRecordListView(APIView):
    def get(self, request, *args, **kwargs):
        sql = """
            SELECT dr.*, b.title as book_title
            FROM books_disposalrecord dr
            JOIN books_book b ON dr.book_id = b.id
            ORDER BY dr.disposal_date DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            records = dictfetchall(cursor)

        for record in records:
            record["book"] = {"title": record.pop("book_title")}

        serializer = DisposalRecordSerializer(records, many=True)
        return Response(serializer.data)


# --- 统计视图 (复杂的聚合查询) ---


class StatisticsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            # 1. 核心数据总览
            cursor.execute("SELECT COUNT(*), SUM(stock) FROM books_book")
            summary_totals = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM books_borrowrecord WHERE status = 'borrowed'")
            current_borrowed_count = cursor.fetchone()

            # 2. 借阅次数最多的 Top 5 图书
            top_5_sql = """
                SELECT b.title, COUNT(br.id) as borrow_count
                FROM books_borrowrecord br
                JOIN books_book b ON br.book_id = b.id
                GROUP BY b.title
                ORDER BY borrow_count DESC
                LIMIT 5
            """
            cursor.execute(top_5_sql)
            top_5_borrowed_books = cursor.fetchall()

            # 3. 按出版社分布
            publisher_sql = """
                SELECT publisher, COUNT(id) as count
                FROM books_book
                GROUP BY publisher
                ORDER BY count DESC
            """
            cursor.execute(publisher_sql)
            publisher_distribution = cursor.fetchall()

            # 4. 每月借阅趋势
            trends_sql = """
                SELECT DATE_FORMAT(borrow_date, '%Y-%m') as month, COUNT(id) as count
                FROM books_borrowrecord
                GROUP BY month
                ORDER BY month
            """
            cursor.execute(trends_sql)
            borrow_trends = cursor.fetchall()

        data = {
            "summary": {
                "total_book_types": summary_totals[0] or 0,
                "total_stock": int(summary_totals[1]) if summary_totals[1] else 0,
                "current_borrowed_count": current_borrowed_count[0] or 0,
            },
            "top_5_borrowed": {
                "labels": [item[0] for item in top_5_borrowed_books],
                "values": [item[1] for item in top_5_borrowed_books],
            },
            "publisher_distribution": [{"name": item[0], "value": item[1]} for item in publisher_distribution],
            "borrow_trends": {
                "labels": [item[0] for item in borrow_trends],
                "values": [item[1] for item in borrow_trends],
            },
        }
        return Response(data)
