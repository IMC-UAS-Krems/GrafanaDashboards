import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from grafana_dashboards.model import DataSourceProvider, Datasource

env = Environment(
    loader=FileSystemLoader("templates/datasources"),
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


def generate_datasources(datasources: dict[str, Datasource]) -> list[dict]:
    sources = []
    template = env.get_template("datasources.json")

    for name, datasource in datasources.items():
        if datasource.provider == DataSourceProvider.Fiware:
            sources.append(generate_datasource_fiware(name, datasource))

        elif datasource.provider == DataSourceProvider.Dataskop:
            sources.append(generate_datasource_dataskop(name, datasource))

        else:
            raise ValueError(f"Unsupported datasource provider: {datasource.provider}")

    return json.loads(template.render(datasources=sources))
