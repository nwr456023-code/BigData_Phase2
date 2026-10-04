import os
import sys
import pandas as pd
from pymongo import MongoClient


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE_PATH = os.path.join(BASE_DIR, "data", "orders_huge_mixed_quality.csv")

print("="*50)
print("1. جاري التحقق من وجود الملف الضخم...")
sys.stdout.flush()

if not os.path.exists(FILE_PATH):
    print(f"خطأ: الملف غير موجود في المسار: {FILE_PATH}")
    sys.exit(1)

file_size_gb = os.path.getsize(FILE_PATH) / (1024**3)
print(f"تم العثور على الملف! الحجم: {file_size_gb:.2f} GB")

# 2. الاتصال بـ MongoDB
print("2. جاري الاتصال بقاعدة البيانات MongoDB...")
sys.stdout.flush()

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["orders_db"]
collection = db["orders"]


CHUNK_SIZE = 100000
print(f"3. جاري بدء معالجة البيانات وضخها على دفعات (حجم الدفعة: {CHUNK_SIZE:,} سجل)...")
sys.stdout.flush()

processed_count = 0

for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE, low_memory=False):
    # إزالة المسافات الزائدة من أسماء الأعمدة وحسب الأحرف الصغيرة
    chunk.columns = chunk.columns.str.strip().str.lower()
    
    # التعرف على اسم عمود الكمية سواء كان qty أو quantity
    qty_col = 'qty' if 'qty' in chunk.columns else ('quantity' if 'quantity' in chunk.columns else None)
    
    if qty_col:
        chunk[qty_col] = pd.to_numeric(chunk[qty_col], errors='coerce').abs().fillna(0).astype(int)
    
    if 'unit_price' in chunk.columns:
        chunk['unit_price'] = pd.to_numeric(chunk['unit_price'], errors='coerce').fillna(0.0)
    
    if 'total_price' in chunk.columns:
        chunk['total_price'] = pd.to_numeric(chunk['total_price'], errors='coerce').fillna(0.0)
        if 'currency' in chunk.columns:
            chunk.loc[chunk['currency'] == 'USD', 'total_price'] *= 530
            chunk.loc[chunk['currency'] == 'USD', 'currency'] = 'YER'
    
    if 'created_at' in chunk.columns:
        chunk['created_at'] = pd.to_datetime(chunk['created_at'], errors='coerce')
    if 'expected_date' in chunk.columns:
        chunk['expected_date'] = pd.to_datetime(chunk['expected_date'], errors='coerce')
    
   
    records = chunk.to_dict('records')
    if records:
        collection.insert_many(records)
        processed_count += len(records)
        print(f"تم ضخ: {processed_count:,} / 30,000,000 سجل إلى MongoDB...")
        sys.stdout.flush()

print("="*50)
print("تمت عملية التنظيف وضخ الـ 30 مليون سجل إلى MongoDB بنجاح كامل!")