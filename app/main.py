from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import Base, engine, SessionLocal
from app.routes.pages import router as pages_router
from app.routes.screen import router as screen_router
from app.routes.resolve import router as resolve_router
from app.routes.cases import router as cases_router
from app.routes.stats import router as stats_router
from app.routes.analyze import router as analyze_router
from app.routes.batch import router as batch_router
from app.routes.query import router as query_router

app = FastAPI(title="Sanction Screening Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages_router)
app.include_router(screen_router)
app.include_router(resolve_router)
app.include_router(cases_router, prefix="/api")
app.include_router(stats_router)
app.include_router(analyze_router)
app.include_router(batch_router)
app.include_router(query_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    try:
        db = SessionLocal()
        db.execute(text("ALTER TABLE cases ADD COLUMN notes TEXT"))
        db.commit()
        db.close()
    except Exception:
        pass
