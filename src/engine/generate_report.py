import json
from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["orders_db"]
collection = db["orders"]

print("جاري استخراج التقرير التجميعي النهائي...")


pipeline = [
    {
        "$group": {
            "_id": "$status",
            "total_orders": {"$sum": 1},
            "total_revenue": {"$sum": "$payment_amount"}
        }
    }
]

results = list(collection.aggregate(pipeline))

report_data = {
    "total_records": collection.count_documents({}),
    "status_summary": results
}


with open("reports/results.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, ensure_ascii=False, indent=4)

print("تم إنشاء التقرير النهائي وحفظه بنجاح في reports/results.json!")