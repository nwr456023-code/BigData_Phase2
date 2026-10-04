import time
import json
from pymongo import MongoClient

# 1. الاتصال بقاعدة البيانات
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["orders_db"]
collection = db["orders"]

print("==================================================")
print("   بدء تنفيذ خطوة الاستعلامات والفهارس و Explain   ")
print("==================================================\n")

# ----------------------------------------------------
# قائمة بالـ 5 استعلامات المطلوبة للمشروع
# ----------------------------------------------------
QUERIES = {
    "query_1_by_status": {"status": "paid"},
    "query_2_by_city": {"city": "Sanaa"},
    "query_3_by_date_range": {
        "created_at": {
            "$gte": "2025-01-01T00:00:00",
            "$lte": "2025-06-30T23:59:59"
        }
    },
    "query_4_compound_status_date": {
        "status": "paid",
        "created_at": {"$gte": "2025-01-01T00:00:00"}
    },
    "query_5_high_value_orders": {
        "payment_amount": {"$gt": 500000}
    }
}

def run_queries():
    """تنفيذ الـ 5 استعلامات وإرجاع عينة من النتائج"""
    print("--- 1. تنفيذ الـ 5 استعلامات المطلوبة ---")
    results = {}
    for name, query in QUERIES.items():
        start = time.time()
        # جلب أول 5 نتائج لكل استعلام
        cursor = list(collection.find(query, {"_id": 0}).limit(5))
        elapsed = (time.time() - start) * 1000
        count = collection.count_documents(query)
        results[name] = {
            "query": str(query),
            "match_count": count,
            "execution_time_ms": round(elapsed, 2),
            "sample": cursor[0] if cursor else None
        }
        print(f"✓ {name}: تم العثور على {count:,} سجل (زمن التنفيذ: {elapsed:.2f} ms)")
    return results

def get_execution_stats(query):
    """إجراء explain('executionStats') لاستعلام معين"""
    explanation = db.command(
        'explain',
        {'find': 'orders', 'filter': query},
        verbosity='executionStats'
    )
    execution_stats = explanation.get('executionStats', {})
    return {
        "executionTimeMillis": execution_stats.get("executionTimeMillis"),
        "totalDocsExamined": execution_stats.get("totalDocsExamined"),
        "nReturned": execution_stats.get("nReturned")
    }

def run_explain_analysis(phase_label):
    """تحليل أداء 3 استعلامات باستخدام explain"""
    print(f"\n--- إجراء تحليل Explain ({phase_label}) ---")
    selected_queries = [
        ("query_1_by_status", QUERIES["query_1_by_status"]),
        ("query_3_by_date_range", QUERIES["query_3_by_date_range"]),
        ("query_4_compound_status_date", QUERIES["query_4_compound_status_date"])
    ]
    
    explain_results = {}
    for name, query in selected_queries:
        stats = get_execution_stats(query)
        explain_results[name] = stats
        print(f"  • [{name}]")
        print(f"    - زمن التنفيذ: {stats['executionTimeMillis']} ms")
        print(f"    - عدد الوثائق المفحوصة (Docs Examined): {stats['totalDocsExamined']:,}")
        print(f"    - عدد السجلات المعادة (Returned): {stats['nReturned']:,}")
    return explain_results

def create_required_indexes():
    """إنشاء الـ 3 الفهارس المطلوبة بما فيها الـ Compound Index"""
    print("\n--- 2. إنشاء الفهارس (Indexes) ---")
    
    # 1. Index منفرد على التاريخ
    print("1) جاري إنشاء Single Index على created_at...")
    collection.create_index("created_at")
    
    # 2. Index منفرد على الحالة
    print("2) جاري إنشاء Single Index على status...")
    collection.create_index("status")
    
    # 3. Compound Index (فهرس مركب) على (status + created_at)
    print("3) جاري إنشاء Compound Index على (status, created_at)...")
    collection.create_index([("status", 1), ("created_at", -1)])
    
    print("✓ تم إنشاء جميع الفهارس بنجاح!")

if __name__ == "__main__":
    # 1. تحليل الأداء قبل الفهارس (إذا كانت الفهارس سابقة، سنقوم بمقارنتها)
    print("أ) قياس الأداء وتقارير Explain قبل/بعد الفهارس:")
    before_stats = run_explain_analysis("المرحلة الحالية")
    
    # 2. إنشاء الفهارس المطلوبة (3 Indexes منها 1 Compound)
    create_required_indexes()
    
    # 3. تحليل الأداء بعد تأكيد وجود الفهارس
    after_stats = run_explain_analysis("بعد تأكيد الفهارس")
    
    # 4. تشغيل الـ 5 استعلامات العامة
    print("\nب) تشغيل الـ 5 استعلامات الرئيسية:")
    queries_summary = run_queries()
    
    # 5. حفظ النتائج في ملف JSON للاستخدام في الـ API والتقارير
    output_data = {
        "explain_before": before_stats,
        "explain_after": after_stats,
        "queries_summary": queries_summary
    }
    
    with open("reports/explain_stats.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print("\n==================================================")
    print("✓ تم حفظ نتائج المقارنة والتقارير بنجاح في reports/explain_stats.json")
    print("==================================================")