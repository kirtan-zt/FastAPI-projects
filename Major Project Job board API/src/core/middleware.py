import logging
import time
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, Any, List
import re 
from src.core.config import BYPASS_MIDDLEWARE_PATHS
from src.core.dependencies import get_db_user_by_username, check_user_role
from src.core import auth
from src.models.users import User, roles

from src.core.dependencies import get_current_user 
from src.core import auth
from src.models.users import User, roles
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, HTTPException

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

#  Logging middleware
async def log_request_response_middleware(request: Request, call_next):
    start_time=time.time() # Marks the time when a request is made
    logger.info(f"Request for {request.method} method started")   # Request logger
    response: Response=await call_next(request)
    process_time=time.time()-start_time # Marks the time when a response is returned
    logger.info(
        f"Response for {request.method} method completed with status code {response.status_code} in {process_time:.2f}s"
    )
    return response 

# Role check Middleware
class RoleAuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app: ASGIApp,
        session_factory: Any, 
        role_map: Dict[str, List[roles]] 
    ):
        super().__init__(app)
        self.session_factory = session_factory
        self.role_map = role_map

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        required_roles: List[roles] | None = None
        for pattern, roles_list in self.role_map.items():
            if re.match(pattern, path):
                required_roles = roles_list
                break

        if request.method == "GET":
            for pattern in BYPASS_MIDDLEWARE_PATHS: # Allow any user to read data
                if re.match(pattern, path):
                    return await call_next(request)

        if required_roles is None:
            return await call_next(request)

        # AUTHENTICATION
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated. Missing Bearer token."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = auth_header.split(" ")[1]
        
        try:
            username = auth.verify_token(token)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # USER RETRIEVAL 
        async with self.session_factory() as session:
            user = await get_db_user_by_username(session, username)
            
            if user is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication successful but user not found in DB."},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            try:
                check_user_role(user, required_roles)
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
                    
        # If all checks pass, proceed to the route
        response = await call_next(request)
        return response