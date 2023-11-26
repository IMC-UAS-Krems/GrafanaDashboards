import logging
from typing import TypeAlias, Callable
import json
import base64
import secrets

from model import Config
from types_resolver import TypesResolver
import logging_setup  # will be executed on import  # noqa: F401

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from panel_gen import (
    generate_bar_chart,
    generate_xy_chart,
    generate_time_series,
    generate_geomap,
    generate_pie_chart,
)

GrafanaModel: TypeAlias = dict

app = FastAPI()
logger = logging.getLogger("grafana_dashboards")
logging.basicConfig(level=logging.INFO)
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


panel_mapping: dict[str, Callable] = {
    "bar_chart": generate_bar_chart,
    "xy_chart": generate_xy_chart,
    "timeseries": generate_time_series,
    "geomap": generate_geomap,
    "pie_chart": generate_pie_chart,
}


def generate_uid() -> str:
    """This function should generate a uid for the dashboard.

    Returns:
        str: uid of the dashboard
    """
    return base64.urlsafe_b64encode(secrets.token_bytes(9)).decode("utf-8").rstrip("=")


@app.get(
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
    uid = generate_uid()

    try:
        with TypesResolver() as tr:
            config_panels = config.application.panels
            for i, name in enumerate(config_panels.keys()):
                panels.append(
                    panel_mapping[config_panels[name].type](
                        id=i,
                        config=config_panels[name],
                        type_resolver=tr,
                        data_source=config.data_sources[config_panels[name].source],
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
            uid=uid,
        )
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
