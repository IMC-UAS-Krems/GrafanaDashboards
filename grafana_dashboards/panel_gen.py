import base64
from enum import Enum
import json


from jinja2 import Environment, FileSystemLoader, select_autoescape
from model import BarChart, Datasource, PieChart, XYChart, TimeSeries, GeoMap
from types_resolver import TypesResolver


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps

class Coordinates(Enum):
    LONGITUDE = {'name': 'lon', 'index': 0}
    LATITUDE = {'name': 'lat', 'index': 1}


def generate_uid() -> str:
    """This function should generate a uid for the panel data source.
    Need to look more into it, for now i am returning a static string

    Returns:
        str: uid of the panel
    """
    return "2RGTUW4Sk"
    # return base64.urlsafe_b64encode(secrets.token_bytes(9)).decode("utf-8").rstrip("=")


def generate_coordiante_field(coordinates:Coordinates) -> dict:
    """This function generates the field for the coordinate of the geomap panel.

    Args:
        i (int): Because the coordinates are stored in a list of [longitude, latitude],
        we need to specify which one we want to query. 0 for longitude, 1 for latitude
        Needs to be made more general, works for location for now
        Don't need type_resolver as the type is always number for coordinates

    Returns:
        dict: field as it is in field.json
    """
    template = env.get_template("field.json")

    return json.loads(
        template.render(
            path = f'$[*].location.value.coordinates[{coordinates.value["index"]}]', 
            name=coordinates.value["name"],
            type="number",
        )
    )


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
    
    return json.loads(
        template.render(
            path = f'$[*].($count({field_name}) > 0 ? {field_name}.value : null)',  # a bit stupid needs to be resolved in the futur, works for now
            name=field_name,
            type=type,
        )
    )


def generate_grid_pos(col: int) -> dict:
    """This function generated the grid position for a panel
    h -> height of the panel
    w -> width of the panel
    x -> x position, = col * w
    y -> y position, = col * h
    For the moment we will store the panels 2 by line
    Grafana dashboards are 24 spaces on x axis.

    Args:
        col (int): Used the id of the panel 

    Returns:
        dict: grid position of the pane as it is in grid_pos.json
    """
    template = env.get_template("grid_pos.json")

    return json.loads(
        template.render(
                h=8,
                w=12,
                x= (col % 2) * 12,
                y = (col // 2) * 8,
            )
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


def generate_xy_chart(
        uid: str,
        id: int,
        config: XYChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str
) -> dict:
    """This function generates the xy chart panel.

    Args:
        uid (str): Unique id of the data source
        id (int): Id of the panel
        config (XYChart): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in xy.json
    """
    template = env.get_template("xy.json")
    return json.loads(
        template.render(
            uid=uid,
            grid_pos= generate_grid_pos(id),
            id = id,
            fields=[
                generate_field(field_name, type_resolver, data_source)
                for field_name in config.traces
            ],
            type=data_source.query.type,
            title=title,
        )
    )


def generate_time_series(
        uid: str,
        id: int,
        config: TimeSeries,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str
) -> dict:
    """This function generates the time series panel.

    Args:
        uid (str): Unique id of the data source
        id (int): Id of the panel
        config (TimeSeries): The type of the panel
        type_resolver (TypesResolver): Used to generate the field. ! does not work for time
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in timeseries.json
    """
    template = env.get_template("timeseries.json")
    return json.loads(
        template.render(
            uid=uid,
            grid_pos= generate_grid_pos(id),
            id = id,
            fields=[
                generate_field(field_name, type_resolver, data_source)
                for field_name in config.traces
            ],
            type=data_source.query.type,
            title=title,
        )
    )


def generate_geomap(
        uid: str,
        id: int,
        config: GeoMap,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str
) -> dict:
    """This function generates the geomap panel.

    Args:
        uid (str): Unique id of the data source
        id (int): Id of the panel
        config (GeoMap): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in geomap.json
    """
    template = env.get_template("geomap.json")
    fields = [
                generate_field(field_name, type_resolver, data_source)
                for field_name in config.data if field_name != 'location'
            ]
    # call generate coordinate field separately 
    fields.append(generate_coordiante_field(Coordinates.LONGITUDE))
    fields.append(generate_coordiante_field(Coordinates.LATITUDE))
    return json.loads(
        template.render(
            uid=uid,
            grid_pos=generate_grid_pos(id),
            id = id,
            layerName = data_source.query.type,
            fields=fields,
            type=data_source.query.type,
            title=title,
        )
    )

