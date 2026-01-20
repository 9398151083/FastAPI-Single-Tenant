import traceback
from jose import JOSEError
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from app.core.ratelimit import rate_limit_exceeded_handler, BLOCK_DURATION


# ----------------- Pagination Validation -----------------
class PaginationValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        page = int(request.query_params.get("page") or "1")
        pageSize = int(request.query_params.get("pageSize") or "100")

        if page < 1 or page > 100000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid page number",
            )
        if pageSize < 1 or pageSize > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid page size",
            )

        return await call_next(request)


# ----------------- Local CORS Middleware -----------------
class CORSMiddlewareLocal(BaseHTTPMiddleware):
    def allow_cors(self, response: Response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response()
            return self.allow_cors(response)

        response = await call_next(request)
        return self.allow_cors(response)


# ----------------- Global Error Handler -----------------
class GlobalErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except RateLimitExceeded as e:
            return await rate_limit_exceeded_handler(request, e)
        except HTTPException as e:
            return self.__build_error_response(request, e.detail, e.status_code)
        except JOSEError as e:
            return self.__build_error_response(
                request, "\n".join(map(str, e.args)), status.HTTP_401_UNAUTHORIZED
            )
        except ValidationError as e:
            return self.__build_error_response(
                request, str(e), status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return self.__build_error_response(
                request,
                "\n".join(map(str, e.args)),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def __build_error_response(self, request: Request, content: str, status_code: int):
        traceback.print_exc()
        if hasattr(request.state, "db"):
            request.state.db.rollback()
        return JSONResponse(
            content={
                "message": content.replace("\n", ": ").strip(),
                "url": str(request.url),
            },
            status_code=status_code,
        )


# ----------------- Setup All Middlewares -----------------
def setup_middlewares(app: FastAPI):
    # Default CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    # Custom middlewares
    app.add_middleware(GlobalErrorHandlerMiddleware)
    app.add_middleware(CORSMiddlewareLocal)
    app.add_middleware(PaginationValidationMiddleware)
