import csv
import time
import json
from datetime import datetime
from config.settings import BATCH_SIZE, DB_NAME, COLLECTIONS
from src.database.mongo_setup import get_mongo_client
from src.quality.rules import QualityRules

class PythonBatchEngine:
    def __init__(self, file_path, id_run):
        self.file_path = file_path
        self.id_run = id_run
        self.client = get_mongo_client()
        self.db = self.client[DB_NAME]

    def run(self):
        start_time = time.time()
        read_rows = 0
        loaded_raw = 0
        count_valid = 0
        count_corrected = 0
        count_quarantine = 0
        count_inserted = 0
        count_updated = 0
        count_unchanged = 0

        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch_raw = []
            
            for row_idx, row in enumerate(reader, start=1):
                read_rows += 1
                
                raw_doc = {
                    "id_run": self.id_run,
                    "file_source": self.file_path,
                    "number_row_source": row_idx,
                    "at_ingested": datetime.utcnow(),
                    "engine_used": "python_batch",
                    "record_raw": row
                }
                batch_raw.append(raw_doc)
                
                cleaned_row, status, corrections, quarantine_reasons = QualityRules.process_record(row)
                
                if len(batch_raw) >= BATCH_SIZE:
                    res = self.db[COLLECTIONS["raw"]].insert_many(batch_raw)
                    loaded_raw += len(res.inserted_ids)
                    batch_raw = []

                if status == "quarantined":
                    count_quarantine += 1
                    quarantine_doc = {
                        "id_run": self.id_run,
                        "record_raw": row,
                        "error_codes": quarantine_reasons,
                        "quarantined_at": datetime.utcnow()
                    }
                    self.db[COLLECTIONS["quarantine"]].insert_one(quarantine_doc)
                else:
                    if status == "corrected":
                        count_corrected += 1
                    else:
                        count_valid += 1
                    
                    validated_doc = {
                        "order_id": cleaned_row.get("order_id"),
                        "customer_id": cleaned_row.get("customer_id"),
                        "details": cleaned_row,
                        "quality_status": status,
                        "corrections": corrections if corrections else None,
                        "last_updated": datetime.utcnow(),
                        "id_run": self.id_run
                    }
                    
                    result = self.db[COLLECTIONS["validated"]].update_one(
                        {"order_id": cleaned_row["order_id"]},
                        {"$set": validated_doc},
                        upsert=True
                    )
                    
                    if result.upserted_id is not None:
                        count_inserted += 1
                    elif result.modified_count > 0:
                        count_updated += 1
                    else:
                        count_unchanged += 1

            if batch_raw:
                res = self.db[COLLECTIONS["raw"]].insert_many(batch_raw)
                loaded_raw += len(res.inserted_ids)

        elapsed = time.time() - start_time
        throughput = read_rows / elapsed if elapsed > 0 else 0

        metrics = {
            "id_run": self.id_run,
            "file_name": self.file_path,
            "used_engine": "python_batch",
            "read_rows": read_rows,
            "loaded_raw": loaded_raw,
            "count_valid": count_valid,
            "count_corrected": count_corrected,
            "count_quarantine": count_quarantine,
            "count_inserted": count_inserted,
            "count_updated": count_updated,
            "count_unchanged": count_unchanged,
            "seconds_elapsed": round(elapsed, 2),
            "throughput": round(throughput, 2)
        }

        with open("reports/results.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4, default=str)

        print("\n--- النتائج والمقاييس ---")
        print(json.dumps(metrics, indent=2, default=str))
        self.client.close()