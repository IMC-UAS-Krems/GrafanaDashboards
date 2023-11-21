import logging
from typing import TypeAlias
import json

import logging_setup  # will be executed on import
from model import Config
from types_resolver import TypesResolver

import uvicorn
from fastapi import FastAPI
from jinja2 import Environment, FileSystemLoader, select_autoescape

from panel_gen import generate_uid, generate_bar_chart, generate_pie_chart, generate_xy_chart, generate_time_series, generate_geomap

GrafanaModel: TypeAlias = dict

app = FastAPI()
logger = logging.getLogger("grafana_dashboards")
logging.basicConfig(level=logging.INFO) 
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


panel_mapping:dict[str, callable] = {
    "bar_chart": generate_bar_chart,
    "xy_chart": generate_xy_chart,
    "timeseries": generate_time_series,
    "geomap": generate_geomap
}


@app.get("/")
async def generate_file(config: Config) -> GrafanaModel:
    """This function generates the grafana dashboard json file.

    Args:
        config (Config): The config file that is used to generate the dashboard

    Returns:
        GrafanaModel: The dashboard as it is in config.json
    """
    template = env.get_template("config.json")
    panels = []
    uid = generate_uid()

    with TypesResolver() as tr:
        config_panels = config.application.panels
        for i, name in enumerate(config_panels.keys()):
            if config_panels[name].type == "pie_chart":
                panels.append(
                    generate_pie_chart(
                        uid= uid,
                        id=i,
                        config=config_panels[name],
                        type_resolver=tr,
                        data_source=config.data_sources[config_panels[name].source],
                        title=name,
                        pie_chart_type=config_panels[name].pie_chart_type
                    )
                )
            else:
                try:
                    panels.append(
                        panel_mapping[config_panels[name].type](
                            uid = uid,
                            id=i,
                            config=config_panels[name],
                            type_resolver=tr,
                            data_source=config.data_sources[config_panels[name].source],
                            title=name,
                        )
                    )
                except KeyError:
                    logger.error(f"Panel type {config_panels[name].type} not supported")
                    raise KeyError(f"Panel type {config_panels[name].type} not supported")

    title = config.service.title
    return json.loads(
        template.render(
            id=1,
            panels = panels,
            title=title,
            uid = uid,
        )
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
