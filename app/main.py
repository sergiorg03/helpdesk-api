from fastapi import FastAPI

app = FastAPI(
    title="HelpDesk API",
    description="REST API for managing technical support tickets.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
