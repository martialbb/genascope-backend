from fastapi import APIRouter
from .chat import router as chat_router
from .eligibility import router as eligibility_router
from .auth import router as auth_router
from .invites import router as invites_router
from .admin import router as admin_router
from .accounts import router as accounts_router
from .account import router as account_router
from .labs import router as labs_router
from .appointments import router as appointments_router
from .users import router as users_router
from .patients import router as patients_router
from .v1.chat_configuration_sync import router as chat_configuration_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(eligibility_router)
api_router.include_router(auth_router)
api_router.include_router(invites_router)
api_router.include_router(admin_router)
api_router.include_router(accounts_router)
api_router.include_router(account_router)
api_router.include_router(labs_router)
api_router.include_router(appointments_router)
api_router.include_router(users_router)
api_router.include_router(patients_router)
api_router.include_router(chat_configuration_router)
