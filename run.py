import sys
import uuid
from src.database.mongo_setup import setup_database_indexes
from src.engine.file_router import route_file
from src.engine.python_batch import PythonBatchEngine

def main():
    file_path = "data/sample_orders.csv" if len(sys.argv) < 2 else sys.argv[1]
    id_run = str(uuid.uuid4())[:8]

    setup_database_indexes()
    engine, _ = route_file(file_path)

    if engine == "python_batch":
        batch_engine = PythonBatchEngine(file_path, id_run)
        batch_engine.run()
    else:
        print("مسار PySpark جاهز للملفات الكبيرة.")

if __name__ == "__main__":
    main()