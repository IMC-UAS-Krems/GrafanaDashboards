import logging
from typing import TypeAlias, Callable
import json
from random import choice

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape

from panel_gen import (
    generate_bar_chart,
    generate_xy_chart,
    generate_time_series,
    generate_geomap,
    generate_pie_chart,
    generate_single_line,
)

from model import Config
import logging_setup  # will be executed on import  # noqa: F401
from types_resolver import TypesResolver

GrafanaModel: TypeAlias = dict

app = FastAPI()
logger = logging.getLogger("grafana_dashboards")
type_resolver = TypesResolver()
logging.basicConfig(level=logging.INFO)
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


panel_mapping: dict[str, Callable] = {
    "bar_chart": generate_bar_chart,
    "xy_chart": generate_xy_chart,
    "timeseries": generate_time_series,
    "geomap": generate_geomap,
    "pie_chart": generate_pie_chart,
    "smartcomm-simpleline-panel": generate_single_line,
}


@app.post(
    "/", response_model=GrafanaModel
)  # NOTE: `response_model` because of https://fastapi.tiangolo.com/tutorial/response-model/#disable-response-model
async def generate_file(config: Config) -> GrafanaModel | JSONResponse:
    """This function generates the grafana dashboard json file.

    Args:
        config (Config): The config file that is used to generate the dashboard

    Returns:
        GrafanaModel: The dashboard as it is in config.json
    """
    template = env.get_template("config.json")
    panels = []

    try:
        config_panels = config.application.panels
        for i, name in enumerate(config_panels.keys()):
            panels.append(
                panel_mapping[config_panels[name].type](
                    id=i,
                    config=config_panels[name],
                    type_resolver=type_resolver,
                    data_source=config.data.sources[config_panels[name].source],
                    title=name,
                )
            )
    except KeyError as e:
        logger.exception(f"KeyError: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error"},
        )

    title = config.service.title

    return json.loads(
        template.render(
            id=1,
            panels=panels,
            title=title,
            uid=None,  
        )
    )


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse("/status")


@app.get("/status")
def status() -> str:
    statuses = ["Single", "In a relationship", "Married", "In love", "It's complicated"]
    return choice(statuses)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)
