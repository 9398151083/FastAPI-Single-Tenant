from fastapi import FastAPI
from app.routes import setup_routes
from app.utils.middlewares import setup_middlewares
from app.core.ratelimit import limiter, BlockIPMiddleware, rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

app = FastAPI()

# Add SlowAPI middleware first
app.add_middleware(SlowAPIMiddleware)

# Add IP block middleware
app.add_middleware(BlockIPMiddleware)

# Setup routes and other middlewares
setup_routes(app)
setup_middlewares(app)

# Exception handler for rate limiting
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Attach limiter to app state for decorators
app.state.limiter = limiter
