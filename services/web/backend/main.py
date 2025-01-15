from fastapi import FastAPI

# from api.routes import papers, search, analysis

app = FastAPI(
    title="OpenImpact API",
    description="Research paper analysis and search API",
    version="0.1.0",
)

# 라우터 등록
# app.include_router(papers.router)
# app.include_router(search.router)
# app.include_router(analysis.router)


@app.get("/")
async def root():
    return {"message": "Welcome to OpenImpact API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
