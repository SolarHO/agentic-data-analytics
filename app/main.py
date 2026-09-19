from fastapi import FastAPI, HTTPException

from app.db.postgres import check_database_connection


app = FastAPI(
    title="AI Data Analytics Platform",
    description="LLM-based automated data analytics platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-data-analytics-platform",
    }


@app.get("/health/db")
def database_health_check():
    try:
        is_connected = check_database_connection()

        if not is_connected:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed",
            )

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {exc}",
        )
