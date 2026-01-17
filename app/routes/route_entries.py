from app.routes import groups_route, invite_routes, register_routes
from . import (
    auth_route,
    task_route,
    expense_route,
    groups_route,
    invite_routes,
)  # Add this

PUBLIC_ROUTES = [auth_route.router, register_routes.router]
PROTECTED_ROUTES = [
    task_route.router,
    expense_route.router,
    groups_route.router,
    invite_routes.router,
    # Add this
]
