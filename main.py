from typing import Optional, Callable

from fastapi import FastAPI, HTTPException, Body, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.routing import APIRoute

from pydantic import BaseModel

from starlette.requests import Request
from starlette.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from raygun4py import raygunprovider

# Raygun client, we need to provide an API key to send notifications.
raygun_client = raygunprovider.RaygunSender("")


class Item(BaseModel):
    title: str
    size: int

class UnhandleExceptionsRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except Exception as exception:
                
                body = await request.json()

                request = {
                    #"headers": request.headers,
                    "hostName": None,
                    "url": request.url.path,
                    "httpMethod": request.method,
                    "ipAddress": request.client.host,
                    "queryString": request.query_params,
                    "form": body,
                    "rawData": None,
                }


                tags = ["env:stg","service:my-api"]

                user_custom_data = {
                    "field": "relevant information"
                }

                # Raygun notification
                httpResult = raygun_client.send_exception(exception=exception,tags=tags, userCustomData=user_custom_data, request=request)

                raise exception

        return custom_route_handler

app = FastAPI()
app.router.route_class = UnhandleExceptionsRoute


@app.exception_handler(Exception)
async def validation_exception_handler(request, exc):
    print(str(exc))
    return PlainTextResponse("Something went wrong - Custom Message", status_code=500)

@app.exception_handler(ZeroDivisionError)
async def validation_exception_handler(request, exc):
    print(str(exc))
    return PlainTextResponse("Custom Response for the ZeroDivisionError", status_code=409)

@app.get("/")
def read_root():
    result = 1 / 0
    return {"Hello": "World"}

@app.post("/items/")
async def create_item(item: Item):
    result = 1 / 0
    return item

@app.get("/items/{item_id}", )
def read_item(item_id: int, q: Optional[str] = None):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")

    return {"item_id": item_id, "q": q}