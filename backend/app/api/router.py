from fastapi import APIRouter

from app.api.v1 import me, shop
from app.api.v1.admin import routes as admin_routes

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(me.router)
api_router.include_router(shop.router)
api_router.include_router(admin_routes.router)
