import mongomock
from pymongo import MongoClient, ASCENDING
from config.settings import MONGO_URI, DB_NAME, COLLECTIONS

_mock_client = None

def get_mongo_client():
    global _mock_client
    try:
       
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
        client.server_info()
        return client
    except Exception:
       
        if _mock_client is None:
            _mock_client = mongomock.MongoClient()
        return _mock_client

def setup_database_indexes():
    client = get_mongo_client()
    db = client[DB_NAME]
    
   
    db[COLLECTIONS["raw"]].create_index([("id_run", ASCENDING), ("number_row_source", ASCENDING)])
    db[COLLECTIONS["validated"]].create_index("order_id", unique=True)
    db[COLLECTIONS["validated"]].create_index("id_run")
    db[COLLECTIONS["quarantine"]].create_index("id_run")
    
    print("تم إعداد فهارس قاعدة البيانات بنجاح.")

if __name__ == "__main__":
    setup_database_indexes()