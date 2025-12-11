import logging
import time
from starlette.requests import Request
from starlette.responses import Response

# logger object 
logger=logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

async def log_request_response_middleware(request: Request, call_next):

    start_time=time.time() # Marks the time when a request is made

    # Request logger
    logger.info(f"Request for {request.method} method started")

    response: Response=await call_next(request)

    process_time=time.time()-start_time # Marks the time when a response is returned

    # Response logger
    logger.info(
        f"Response for {request.method} method completed with status code {response.status_code} in {process_time:.2f}s"
    )

    return response 