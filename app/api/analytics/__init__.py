from .analytics import *

analytics_router = APIRouter(prefix="/analytics", tags=["数据分析"])

analytics_router.include_router(analytics.router) 