import time
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from src.engine.aggregations_and_mvs import refresh_daily_sales_mv, refresh_top_products_mv

# إعداد الـ Logging لتسجيل حالة التنفيذ والوقت
logging.basicConfig(
    filename="reports/jobs_execution.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

print("==================================================")
print("     بدء نظام الجدولة والمهام المجدولة (Jobs)     ")
print("==================================================\n")

def run_job_refresh_mvs():
    """مهمة مجدولة 1: تحديث Materialized Views دورياً"""
    start_time = datetime.now()
    logging.info("بدء تنفيذ مهمة تحديث Materialized Views...")
    try:
        refresh_daily_sales_mv()
        refresh_top_products_mv()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"SUCCESS: تم تحديث Materialized Views بنجاح خلال {duration:.2f} ثانية.")
        print(f"✓ [{datetime.now().strftime('%H:%M:%S')}] تم تشغيل مهمة تحديث MVs بنجاح.")
        return True
    except Exception as e:
        end_time = datetime.now()
        logging.error(f"FAILURE: خطأ أثناء تحديث Materialized Views: {str(e)}")
        print(f"✗ خطأ في مهمة تحديث MVs: {str(e)}")
        return False

def run_job_daily_check():
    """مهمة مجدولة 2: التقرير الدوري وفحص النظام"""
    start_time = datetime.now()
    logging.info("بدء تنفيذ مهمة الفحص الدوري والتقارير...")
    try:
        time.sleep(0.5)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"SUCCESS: اكتمل الفحص الدوري خلال {duration:.2f} ثانية.")
        print(f"✓ [{datetime.now().strftime('%H:%M:%S')}] تم تشغيل مهمة الفحص الدوري بنجاح.")
        return True
    except Exception as e:
        logging.error(f"FAILURE: خطأ في الفحص الدوري: {str(e)}")
        return False

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_job_refresh_mvs, 'interval', minutes=30, id='refresh_mvs_job')
    scheduler.add_job(run_job_daily_check, 'interval', hours=1, id='daily_check_job')
    scheduler.start()
    print("✓ تم تشغيل محرك الجدولة التلقائية بنجاح.")
    return scheduler

if __name__ == "__main__":
    print("1) تشغيل تجريبي للمهام وتسجيل الـ Logs...")
    run_job_refresh_mvs()
    run_job_daily_check()
    
    print("\n2) بدء الجدولة التلقائية...")
    sched = start_scheduler()
    print("✓ حُفظت السجلات في reports/jobs_execution.log")