import json
from pymongo import MongoClient

# الاتصال بقاعدة البيانات
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["orders_db"]
collection = db["orders"]

print("==================================================")
print("   بدء تنفيذ التجميعات والـ Materialized Views   ")
print("==================================================\n")

# ----------------------------------------------------
# 1. التجميعات الـ 5 المطلوبة (Aggregations)
# ----------------------------------------------------

def get_sales_by_city():
    pipeline = [
        {"$limit": 100000},
        {"$group": {"_id": "$city", "total_sales": {"$sum": "$payment_amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total_sales": -1}},
        {"$limit": 10}
    ]
    return list(collection.aggregate(pipeline))

def get_top_products():
    pipeline = [
        {"$limit": 100000},
        {"$group": {"_id": "$items_json", "total_orders": {"$sum": 1}, "total_revenue": {"$sum": "$payment_amount"}}},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 10}
    ]
    return list(collection.aggregate(pipeline))

def get_top_customers():
    pipeline = [
        {"$limit": 100000},
        {"$group": {"_id": "$customer_id", "customer_name": {"$first": "$customer_name"}, "total_spent": {"$sum": "$payment_amount"}, "orders_count": {"$sum": 1}}},
        {"$sort": {"total_spent": -1}},
        {"$limit": 10}
    ]
    return list(collection.aggregate(pipeline))

def get_sales_by_period():
    pipeline = [
        {"$limit": 100000},
        {"$group": {"_id": {"$substr": ["$created_at", 0, 7]}, "monthly_sales": {"$sum": "$payment_amount"}, "total_orders": {"$sum": 1}}},
        {"$sort": {"_id": -1}}
    ]
    return list(collection.aggregate(pipeline))

def get_orders_by_status():
    pipeline = [
        {"$limit": 100000},
        {"$group": {"_id": "$status", "count": {"$sum": 1}, "total_value": {"$sum": "$payment_amount"}}}
    ]
    return list(collection.aggregate(pipeline))

# ----------------------------------------------------
# 2. العروض المادية والتحديث التزايدي (Materialized Views)
# ----------------------------------------------------

def refresh_daily_sales_mv():
    """تحديث تزايدي لـ Materialized View المبيعات اليومية"""
    mv_collection = db["mv_daily_sales_summary"]
    
    last_record = mv_collection.find_one(sort=[("_id", -1)])
    match_stage = {}
    if last_record and "_id" in last_record:
        match_stage = {"created_at": {"$gt": last_record["_id"]}}

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})
        
    pipeline.extend([
        {"$limit": 100000},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},
            "daily_revenue": {"$sum": "$payment_amount"},
            "orders_count": {"$sum": 1}
        }},
        {"$merge": {
            "into": "mv_daily_sales_summary",
            "on": "_id",
            "whenMatched": "replace",
            "whenNotMatched": "insert"
        }}
    ])
    
    collection.aggregate(pipeline)
    print("✓ تم تحديث Materialized View (daily_sales_summary) بنجاح!")

def refresh_top_products_mv():
    """تحديث Materialized View لأفضل المنتجات"""
    pipeline = [
        {"$limit": 100000},
        {"$group": {
            "_id": "$items_json",
            "total_sold_value": {"$sum": "$payment_amount"},
            "times_ordered": {"$sum": 1}
        }},
        {"$sort": {"total_sold_value": -1}},
        {"$limit": 50},
        {"$merge": {
            "into": "mv_top_products_summary",
            "on": "_id",
            "whenMatched": "replace",
            "whenNotMatched": "insert"
        }}
    ]
    collection.aggregate(pipeline)
    print("✓ تم تحديث Materialized View (top_products_summary) بنجاح!")

if __name__ == "__main__":
    print("1) جاري إنشاء/تحديث الـ Materialized Views...")
    refresh_daily_sales_mv()
    refresh_top_products_mv()

    print("\n2) جاري تشغيل وحفظ التقارير التجميعية الـ 5...")
    all_aggregations = {
        "sales_by_city": get_sales_by_city(),
        "top_products": get_top_products(),
        "top_customers": get_top_customers(),
        "sales_by_period": get_sales_by_period(),
        "orders_by_status": get_orders_by_status()
    }

    with open("reports/aggregations_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_aggregations, f, ensure_ascii=False, indent=4)

    print("\n==================================================")
    print("✓ تم حفظ نتائج كافة التقارير التجميعية بنجاح في reports/aggregations_summary.json")
    print("==================================================")