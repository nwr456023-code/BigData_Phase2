import os
import json
import subprocess
from fastapi import FastAPI, HTTPException

# استيراد الوظائف الجاهزة من محركات المشروع
from src.engine.aggregations_and_mvs import (
    get_sales_by_city,
    get_top_products,
    get_top_customers,
    get_sales_by_period,
    get_orders_by_status,
    refresh_daily_sales_mv,
    refresh_top_products_mv
)
from src.engine.scheduler_jobs import run_job_refresh_mvs, run_job_daily_check

app = FastAPI(
    title="Big Data Phase 2 API",
    description="واجهة التشغيل الموحدة لاختبار وظائف البيانات الضخمة",
    version="1.0.0"
)

# 1. GET /health
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Big Data Pipeline API"}

# 2. POST /ingest
@app.post("/ingest")
def trigger_ingestion():
    try:
        res = subprocess.run(["python", "src/engine/spark_engine.py"], capture_output=True, text=True)
        return {"status": "success", "message": "Ingestion completed successfully", "output": res.stdout[:200]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. POST /indexes
@app.post("/indexes")
def create_indexes():
    try:
        res = subprocess.run(["python", "src/engine/queries_and_indexes.py"], capture_output=True, text=True)
        return {"status": "success", "message": "Indexes and Explain stats generated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. GET /queries & GET /queries/{name}
@app.get("/queries")
def get_all_queries():
    if os.path.exists("reports/explain_stats.json"):
        with open("reports/explain_stats.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("queries_summary", {})
    return {"message": "No query stats found. Run POST /indexes first."}

@app.get("/queries/{name}")
def get_query_by_name(name: str):
    queries = get_all_queries()
    if name in queries:
        return queries[name]
    raise HTTPException(status_code=404, detail=f"Query '{name}' not found")

# 5. GET /aggregations & GET /aggregations/{name}
@app.get("/aggregations")
def get_all_aggregations():
    return {
        "sales_by_city": get_sales_by_city(),
        "top_products": get_top_products(),
        "top_customers": get_top_customers(),
        "sales_by_period": get_sales_by_period(),
        "orders_by_status": get_orders_by_status()
    }

@app.get("/aggregations/{name}")
def get_aggregation_by_name(name: str):
    aggs = {
        "sales_by_city": get_sales_by_city,
        "top_products": get_top_products,
        "top_customers": get_top_customers,
        "sales_by_period": get_sales_by_period,
        "orders_by_status": get_orders_by_status
    }
    if name in aggs:
        return aggs[name]()
    raise HTTPException(status_code=404, detail=f"Aggregation '{name}' not found")

# 6. POST /refresh-mv
@app.post("/refresh-mv")
def refresh_materialized_views():
    try:
        refresh_daily_sales_mv()
        refresh_top_products_mv()
        return {"status": "success", "message": "Materialized Views refreshed incrementally."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. GET /jobs & POST /jobs/{name}/run
@app.get("/jobs")
def list_scheduled_jobs():
    return {
        "jobs": [
            {"name": "refresh_mvs_job", "interval": "30 minutes", "description": "تحديث الـ Materialized Views"},
            {"name": "daily_check_job", "interval": "1 hour", "description": "الفحص الدوري والتقارير"}
        ]
    }

@app.post("/jobs/{name}/run")
def run_job_manually(name: str):
    if name == "refresh_mvs_job":
        success = run_job_refresh_mvs()
        return {"status": "executed", "job": name, "success": success}
    elif name == "daily_check_job":
        success = run_job_daily_check()
        return {"status": "executed", "job": name, "success": success}
    else:
        raise HTTPException(status_code=404, detail=f"Job '{name}' not found")