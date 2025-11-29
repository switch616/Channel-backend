from .auth import *
from .captcha import *
from .profile import *
from .follow import *

user_router = APIRouter(prefix="/user", tags=["用户"])

user_router.include_router(auth.router)
user_router.include_router(captcha.router)
user_router.include_router(profile.router)
user_router.include_router(follow.router)