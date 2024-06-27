import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from grafana_dashboards.model import DataSourceProvider, Datasource

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


def generate_datasource_fiware(name: str, datasource: Datasource) -> dict:
    template = env.get_template("datasource_fiware.json")

    return json.loads(
        template.render(
            name=name,
            url=datasource.uri,
            uid=datasource.uid,
        )
    )


def generate_datasource_dataskop(name: str, datasource: Datasource) -> dict:
    template = env.get_template("datasource_dataskop.json")

    return json.loads(
        template.render(
            name=name,
            url=datasource.uri,
            uid=datasource.uid,
            token=datasource.config.token,
        )
    )


def generate_datasource(name: str, datasource: Datasource) -> dict:
    if datasource.provider == DataSourceProvider.Fiware:
        return generate_datasource_fiware(name, datasource)

    elif datasource.provider == DataSourceProvider.Dataskop:
        return generate_datasource_dataskop(name, datasource)

    else:
        raise ValueError(f"Unsupported datasource provider: {datasource.provider}")
