import os
from config.settings import SMALL_FILE_THRESHOLD_MB

def route_file(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"الملف غير موجود: {file_path}")
    
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb <= SMALL_FILE_THRESHOLD_MB:
        engine = "python_batch"
        reason = f"حجم الملف ({file_size_mb:.2f} MB) أصغر من أو يساوي الحد الأدنى ({SMALL_FILE_THRESHOLD_MB} MB)."
    else:
        engine = "pyspark"
        reason = f"حجم الملف ({file_size_mb:.2f} MB) يتجاوز الحد الأدنى ({SMALL_FILE_THRESHOLD_MB} MB)."
        
    print(f"\n--- [File Router] ---")
    print(f"مسار الملف: {file_path}")
    print(f"الحجم: {file_size_mb:.2f} MB")
    print(f"المحرك المختار: {engine}")
    print(f"السبب: {reason}\n")
    
    return engine, file_size_mb