from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.api.routes.tickets import router as tickets_router
from app.api.routes.comments import router as comments_router

app = FastAPI(
    title="HelpDesk API",
    description="REST API for managing technical support tickets.",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(comments_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
