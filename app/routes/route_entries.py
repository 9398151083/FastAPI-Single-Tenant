from app.routes import (
    auth_route,
    register_routes,
    task_route,
    expense_route,
    groups_route,
    invite_routes,
    websocket_routes,
    notification_routes,  # ✅ ADD THIS
)

PUBLIC_ROUTES = [auth_route.router, register_routes.router]
PROTECTED_ROUTES = [
    task_route.router,
    expense_route.router,
    groups_route.router,
    invite_routes.router,
    websocket_routes.router,
    notification_routes.router,  # ✅ ADD THIS
]
