from fastapi import APIRouter

from app.api.routes.auth import router as auth
from app.api.routes.cases import router as cases
from app.api.routes.demo import router as demo
from app.api.routes.gmail import router as gmail
from app.api.routes.health import router as health
from app.api.routes.intelligence import router as intelligence
from app.api.routes.jobs import router as jobs
from app.api.routes.operations import router as operations
from app.api.routes.shopify import router as shopify
from app.api.routes.system import router as system

router = APIRouter()
router.include_router(auth, prefix="/auth", tags=["Auth"])
router.include_router(health)
router.include_router(demo, prefix="/demo", tags=["Demo"])
router.include_router(cases, prefix="/cases", tags=["Cases"])
router.include_router(shopify, prefix="/shopify", tags=["Shopify"])
router.include_router(gmail, prefix="/gmail", tags=["Gmail"])
router.include_router(jobs, prefix="/jobs", tags=["Jobs"])
router.include_router(operations, tags=["Operations"])
router.include_router(intelligence, tags=["Intelligence"])
router.include_router(system, tags=["System"])
