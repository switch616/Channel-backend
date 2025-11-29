from .interaction import *

interaction_router = APIRouter(prefix="/interaction", tags=["交互"])

interaction_router.include_router(interaction.router) 