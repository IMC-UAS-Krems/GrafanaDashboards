import logging
from typing import TypeAlias, Callable
import json

from model import Config
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


panel_mapping: dict[str, Callable] = {
    "bar_chart": generate_bar_chart,
    "xy_chart": generate_xy_chart,
    "timeseries": generate_time_series,
    "geomap": generate_geomap,
    "pie_chart": generate_pie_chart,
}


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

    try:
        config_panels = config.application.panels
        for i, name in enumerate(config_panels.keys()):
            panels.append(
                panel_mapping[config_panels[name].type](
                    id=i,
                    config=config_panels[name],
                    type_resolver=type_resolver,
                    # using context manager `with TypesResolver()..` was a stupid idea at a second
                    # thought, so now it's just a class (created at top of
                    # file). Nothing changes for you (it works the same as
                    # before)
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
            uid=None,  # generate_uid() is not needed, none works fine but is not taking it from fix_datasource.sh
            # idk if is supposed to take it from there or not
            #
            # Answer: this is not related to the datasource, but to the dashboard.
            # fix_datasource.sh is supposed to be used to set the uid of the
            # new datasouce because when you are adding one, grafana will
            # generate a random uid for it, and this will cause some issues
            # (you will have to set the right uid (the one that grafana
            # created) manually for every dashboard) setting uid to None will
            # make grafana generate a random one, so it's fine
        )
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
