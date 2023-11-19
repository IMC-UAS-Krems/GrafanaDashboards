import base64
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from model import BarChart, Datasource, PieChart
from types_resolver import TypesResolver


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps

def generate_uid() -> str:
    """This function should generate a uid for the panel data source.
    Need to look more into it, for now i am returning a static string

    Returns:
        str: uid of the panel
    """
    return "2RGTUW4Sk"
    # return base64.urlsafe_b64encode(secrets.token_bytes(9)).decode("utf-8").rstrip("=")


def generate_field(field_name: str, types_resolver: TypesResolver, data_source: Datasource) -> dict:
    """This function generates a field for a panel.
    It uses the field.json template to generate the field.

    Args:
        field_name (str): Name of the field/the element that we want to query
        types_resolver (TypesResolver): From the types_resolver.py file. The field type is resolved using this object
        data_source (Datasource): From the model.py file. The data source is used to get the type of the query

    Returns:
        dict: field as it is in field.json
    """
    template = env.get_template("field.json")
    type = types_resolver.resolve(data_source.query.type, field_name, data_source.uri)

    if not type:
        type = "auto"
    field = template.render(
            path = f'$[*].($count({field_name}) > 0 ? {field_name}.value : null)',  # a bit stupid needs to be resolved in the futur, works for now
            name=field_name,
            type=type,
        )
    return json.loads(
        field
    )

def generate_grid_pos(col: int) -> dict:
    """This function generated the grid position for a panel
    h -> height of the panel
    w -> width of the panel
    x -> x position, = col * w
    y -> y position, = col * h

    Args:
        col (int): Used the id of the panel 

    Returns:
        dict: grid position of the pane as it is in grid_pos.json
    """
    template = env.get_template("grid_pos.json")
    pos = template.render(
                h=8,
                w=12,
                x=col * 12,
                y = col * 8,
            )
    return json.loads(
        pos
    )

def generate_bar_chart(
        uid: str,
        id: int,
        config: BarChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str
) -> dict:
    """This function generates the bar chart panel.

    Args:
        uid (str): The uid of the data source
        id (int): The id of the panel
        config (BarChart): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in barchart.json
    """
    template = env.get_template("barchart.json")
    return json.loads(
        template.render(
            uid=uid,
            grid_pos= generate_grid_pos(id),
            id = id,
            xField=config.traces[0],
            fields=[
                generate_field(field_name, type_resolver, data_source)
                for field_name in config.traces
            ],
            type=data_source.query.type,
            title=title,
        )
    )

def generate_pie_chart(
        uid: str,
        id: int,
        config: PieChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
        pie_chart_type: str
) -> dict:
    """This function generates the pie chart panel.

    Args:
        uid (str): Unique id of the data source
        id (int): Id of the panel
        config (PieChart): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel
        pie_chart_type (str): The type of the pie chart

    Returns:
        dict: The fields of the panel as it is in piechart.json
    """
    template = env.get_template("piechart.json")

    return json.loads(
        template.render(
            uid=uid,
            grid_pos= generate_grid_pos(id),
            id = id,
            pie_chart_type=pie_chart_type, 
            fields=[
                generate_field(field_name, type_resolver, data_source)
                for field_name in config.traces
            ],
            type=data_source.query.type,
            title=title, 
        )
    )