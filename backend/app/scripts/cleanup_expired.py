from app.db.session import SessionLocal
from app.services.retention import cleanup_expired

if __name__ == "__main__":
    with SessionLocal() as db:
        print({"deleted_cases": cleanup_expired(db)})
