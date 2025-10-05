from typing import TypedDict


class BalenaServiceState(TypedDict):
    status: str
    releaseId: int
    downloadProgress: str


class BalenaAppState(TypedDict):
    appId: int
    appName: str
    commit: str
    services: dict[str, BalenaServiceState]
