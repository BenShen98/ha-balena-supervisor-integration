"""Mock Balena Supervisor API for testing Home Assistant container control.

This module provides a FastAPI app that simulates the Balena Supervisor endpoints
for application state and container service control (start, stop, restart).
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import uvicorn
from starlette.background import BackgroundTask
from typing import Any, Dict
import asyncio
import random
from fastapi.responses import JSONResponse

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_balena")

# Simple in-memory container state
appName = "tst"
state = {
    appName: {
        "appId": 123,
        "commit": "fdsghjklerwthyjuk",
        "services": {
            "ha": {
                "status": "Running",
                "releaseId": 345,
                "downloadProgress": None,
            },
            "test1": {
                "status": "Running",
                "releaseId": 345,
                "downloadProgress": None,
            },
            "test2": {
                "status": "Running",
                "releaseId": 345,
                "downloadProgress": None,
            },
        },
    }
}


def log_info(url, req_body, res_body):
    logger.info(
        "request \n\t URL: %s, \n\t request: %s \n\t response: %s \n\t state: %s",
        url,
        req_body,
        res_body,
        state,
    )


@app.middleware("http")
async def some_middleware(request: Request, call_next):
    req_body = await request.body()
    # await set_body(request, req_body)  # not needed when using FastAPI>=0.108.0.
    response = await call_next(request)

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    res_body = b"".join(chunks)

    task = BackgroundTask(log_info, request.url, req_body, res_body)
    return Response(
        content=res_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=task,
    )


@app.post("/")
def main(payload: Dict[Any, Any]):
    return payload


class ContainerControlRequestBody(BaseModel):
    """Request body for stop/start/restart a container service."""

    serviceName: str  # noqa: N815


@app.get("/v2/applications/state")
async def get_applications_state():
    """Mocking the /v2/applications/state endpoint of Balena Supervisor."""
    return state


async def transition_service_state(
    service_name: str, state_sequence: list[str], delays: list[float]
):
    """Transition a service through a sequence of states with delays."""
    appstate = state[appName]
    for i, next_state in enumerate(state_sequence):
        if i > 0:  # Skip delay before first state change
            await asyncio.sleep(delays[i - 1])
        appstate["services"][service_name]["status"] = next_state
        logger.info(f"Service {service_name} transitioned to {next_state}")


@app.post("/v2/applications/{appid}/{action}")
async def control_application(
    appid: int, action: str, body: ContainerControlRequestBody
):
    """Mocking the /v2/applications/{appid}/start-service, stop-service, restart-service endpoint of Balena Supervisor."""
    if appid != state[appName]["appId"]:
        raise HTTPException(status_code=404, detail="App not found")

    if action not in ["start-service", "stop-service", "restart-service"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    service_name = body.serviceName
    if service_name not in state[appName]["services"]:
        raise HTTPException(status_code=404, detail="Service not found")

    current_status = state[appName]["services"][service_name]["status"]

    if action == "start-service":
        if current_status in ["Exited"]:
            # Start a background task to transition: Exited/Stopped -> Installing -> Running
            delays = [
                random.uniform(0.5, 2.0)
            ]  # Random delay between Installing and Running
            asyncio.create_task(
                transition_service_state(
                    service_name, ["Installing", "Running"], delays
                )
            )
            return JSONResponse(content="OK", status_code=200)
        else:
            return JSONResponse(
                content="Service already running or in transition", status_code=200
            )

    elif action == "stop-service":
        if current_status == "Running":
            # Start a background task to transition: Running -> Stopping -> Exited -> Stopped
            delays = [random.uniform(0.5, 1.5), random.uniform(0.5, 1.0)]
            asyncio.create_task(
                transition_service_state(service_name, ["Stopping", "Exited"], delays)
            )
            return JSONResponse(content="OK", status_code=200)
        else:
            return JSONResponse(
                content="Service not running or already in transition", status_code=200
            )

    elif action == "restart-service":
        if current_status == "Running":
            # Start a background task to transition: Running -> Exited -> Installing -> Running
            delays = [random.uniform(0.5, 1.0), random.uniform(1.0, 2.5)]
            asyncio.create_task(
                transition_service_state(
                    service_name, ["Exited", "Installing", "Running"], delays
                )
            )
            return JSONResponse(content="OK", status_code=200)
        else:
            return JSONResponse(
                content="Service not running or already in transition", status_code=200
            )

    return JSONResponse(content="OK", status_code=200)


if __name__ == "__main__":
    host = os.environ.get("MOCK_SUPERVISOR_HOST", "0.0.0.0")
    port = int(os.environ.get("BALENA_SUPERVISOR_PORT", "8080"))
    auth_key = os.environ.get("BALENA_SUPERVISOR_API_KEY", "testkey")
    uvicorn.run("mock_balena_supervisor:app", host=host, port=port, reload=True)
