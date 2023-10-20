import logging
from typing import TypeAlias

import uvicorn
from fastapi import FastAPI

from model import Config
import logging_setup # will be executed on import

GrafanaModel: TypeAlias = dict

app = FastAPI()
logger = logging.getLogger("grafana_dashboards")


@app.get("/")
async def root(config: Config) -> GrafanaModel:
    return {}


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
