"""API routers."""

from src.routers.profiles import router as profiles_router
from src.routers.devices import router as devices_router
from src.routers.tasks import router as tasks_router
from src.routers.fingerprints import router as fingerprints_router
from src.routers.stream import router as stream_router
from src.routers.snapshots import router as snapshots_router
from src.routers.chat import router as chat_router
from src.routers.debug import router as debug_router
from src.routers.settings import router as settings_router
from src.routers.proxies import router as proxies_router
from src.routers.connectors import router as connectors_router
from src.routers.admin import router as admin_router
from src.routers.apps import router as apps_router

__all__ = [
    "profiles_router",
    "devices_router",
    "tasks_router",
    "fingerprints_router",
    "stream_router",
    "snapshots_router",
    "chat_router",
    "debug_router",
    "settings_router",
    "proxies_router",
    "connectors_router",
    "admin_router",
    "apps_router",
]
