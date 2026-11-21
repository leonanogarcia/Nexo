from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import UI_ASSETS, paths
from .i18n import get_active_language, translate_api_message
from .routes.common import get_database_health
from .routes import documents_ai, home_bi, materials, products, recipes, settings

app = FastAPI(title="Nexo API", version="2.1.1")


@app.exception_handler(HTTPException)
async def localized_http_exception_handler(_request: Request, exc: HTTPException):
    lang = get_active_language()
    detail = translate_api_message(exc.detail, lang)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=exc.headers)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def storage_guard_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        path = request.url.path
        guarded_prefixes = ("/api/materials", "/api/recipes", "/api/products", "/api/custom-units", "/api/purchases")
        if path.startswith(guarded_prefixes) and not path.endswith("/delete"):
            health = get_database_health()
            if not health["can_write"]:
                raw_detail = " ".join(health["health_reasons"]) or "Sem espaço suficiente em disco ou teto do banco atingido."
                detail = translate_api_message(raw_detail)
                return JSONResponse(status_code=507, content={"detail": detail})
    return await call_next(request)


if UI_ASSETS.exists():
    app.mount("/ui_assets", StaticFiles(directory=str(UI_ASSETS)), name="ui_assets")

app.include_router(settings.router)
app.include_router(materials.router)
app.include_router(recipes.router)
app.include_router(products.router)
app.include_router(home_bi.router)
app.include_router(documents_ai.router)

FRONTEND_DIST = paths.RESOURCE_DIR / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
