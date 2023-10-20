from os import walk
from typing import TypeAlias

import uvicorn
from fastapi import FastAPI

from .model import Config

GrafanaModel: TypeAlias = dict

app = FastAPI()


@app.get("/")
async def root(config: Config) -> GrafanaModel:
    return {}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0:8000", reload=True)
