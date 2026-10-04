import os

# size
SMALL_FILE_THRESHOLD_MB = float(os.getenv("SMALL_FILE_THRESHOLD_MB", 200.0))


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "order_pipeline"


COLLECTIONS = {
    "raw": "orders_raw",
    "validated": "orders_validated",
    "quarantine": "orders_quarantine"
}


BATCH_SIZE = 1000