"""
This module is responsible for generating the fields for the queries in the Grafana dashboard.
The fields are used to query the data from the datasource.
Because some fields are different for different panels, we have multiple functions.

Returns:
    dict | tuple[list[dict], list | None]: The fields as they are in field.json
    or a list of fields and a list of groups
"""

from enum import Enum
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .model import Datasource
from .types_resolver import Keys, TypesResolver
# from .panel_gen import generate_special_value_field_for_dataskope, bar_field


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


class Coordinates(Enum):
    LONGITUDE = {"name": "lon", "index": 0}
    LATITUDE = {"name": "lat", "index": 1}

def generate_grid_pos(col: int, panel_type: str) -> dict:
    """This function generated the grid position for a panel
    h -> height of the panel
    w -> width of the panel
    x -> x position, = col * w
    y -> y position, = col * h
    Depending on the panel type, the height and width are different.
    For the moment, the only panel that has a different height and width is the calendar panel.

    Args:
        col (int): Used the id of the panel

    Returns:
        dict: grid position of the pane as it is in grid_pos.json
    """
    template = env.get_template("grid_pos.json")

    if panel_type == "smartcomm-calendar-panel":
        h = 32
        w = 24
        x = (col % 2) * 24
    elif panel_type == "smartcomm-multiplelinechart-panel":
        h = 16
        w = 24
        x = (col % 2) * 24
    elif panel_type == "smartcomm-extremevalues-panel":
        h = 16
        w = 12
        x = (col % 2) * 12
    elif panel_type == "smartcomm-bulletgraph-panel":
        h = 10
        w = 24
        x = (col % 2) * 24
    else:
        h = 8
        w = 12
        x = (col % 2) * 12

    return json.loads(
        template.render(
            h=h,
            w=w,
            x=x,
            y=(col // 2) * 8,  # assuming that other panels are 8 high
        )
    )

def generate_special_value_field_for_dataskope(
    field_name: str,
    types_resolver: TypesResolver,
    data_source: Datasource,
    value_name: str,
) -> dict:
    data_type = types_resolver.resolve_dataskop(
        data_source.uri,
        data_source.config.token,
        data_source.config.measurements[field_name],
    )

    return json.loads(
        env.get_template("field.json").render(
            path=f"$[*].measurementResults.${data_type}(value)",
            language="jsonata",
            name=value_name,
            type=data_type,
        )
    )


def bar_field(
    field_name: str,
    types_resolver: TypesResolver,
    data_source: Datasource,
    value_name: str,
) -> dict:
    data_type = types_resolver.resolve_dataskop(
        data_source.uri,
        data_source.config.token,
        data_source.config.measurements[field_name],
    )

    field_name = field_name.split("_")[0]

    return json.loads(
        env.get_template("field.json").render(
            path=f'$[*].measurementResults.($count(value) > 0 ? "{value_name}" :  "{value_name}")',
            language="jsonata",
            name="Fields",
            type="string",
        )
    )

def generate_target_dataskop(
    field_name: str,  # example: "O3"
    index_field: int,  # between 0 and 3
    types_resolver: TypesResolver,
    data_source: Datasource,
    panel_type: str,
    hide: bool = False,
    location: str | None = None,  # example: "Pza. de España"
    with_time: bool = True,
    geomap: bool = False,
    special_value: bool = False,
    bar: bool = False,
    is_fhstp: bool = True,
) -> dict:
    """This function generates the target for multiple smartcomm panels.
    Each target is a group of queries for a specific location and a specific field.
    Currently the plugin accepts only 4 fields: "Luftfeuchtigkeit", "Temperatur", "Feinstaub", "Luftdruck"
    Because we cannot have our own attributes we mask them with the ones that are available in the plugin.

    Args:
        location (str): The station name
        field_name (str): The field name that we want to query
        index_field (int): The index of the field, needed for extreme values panel
        data_source (Datasource): Used to generate the field and the type of the query
        hide (bool, optional): It is used as a fix for the bullet graph panel. Defaults to False.

    Returns:
        dict: The fields of the panel as it is in target.json
    """
    attributes = ["Temperatur", "Luftfeuchtigkeit", "Feinstaub", "Luftdruck"]
    dataskop = env.get_template("dataskop.json")
    fields = []

    # because the label of the target is location-attribute we need to connect them
    # in the new version we have pannels which expect dash but others expect underscore
    if is_fhstp:
        ref_id = (
            location + "_" + attributes[index_field]
            if location
            else attributes[index_field]
        )
    else:
        ref_id = field_name

    if special_value:
        fields.append(
            generate_special_value_field_for_dataskope(
                field_name,
                types_resolver,
                data_source,
                attributes[index_field] if is_fhstp else field_name,
            )
        )
        if bar:
            fields.append(
                bar_field(
                    field_name,
                    types_resolver,
                    data_source,
                    attributes[index_field] if is_fhstp else field_name,
                )
            )
    else:
        fields.append(
            generate_value_field_for_dataskope(field_name, types_resolver, data_source)
        )

    if with_time:
        fields.append(generate_time_field_for_dataskope())

    if geomap:
        fields.append(generate_coordinate_field_dataskope("longitude"))
        fields.append(generate_coordinate_field_dataskope("latitude"))

    return json.loads(
        dataskop.render(
            datasource_uid=data_source.uid,
            fields=fields,
            hide=hide,
            ref_id=ref_id,
            measurement_id=data_source.config.measurements[field_name],
        )
    )

def generate_time_field_for_single_line(field_name: str) -> dict:
    """This function is for the moment only for the single line panel.
    Generates the field for the time field which needs to be jsonpath.

    Args:
        field_name (str): The name of the field

    Returns:
        dict: field as it is in field.json
    """
    template = env.get_template("field.json")

    return json.loads(
        template.render(
            path=f"$[*].{field_name}.value",
            language="jsonpath",
            name=field_name,
            type="time",
        )
    )


# def generate_field_calendar(
#     location: str,
#     field_name: str,
#     types_resolver: TypesResolver,
#     data_source: Datasource,
# )-> dict:
#     """This function generates a field for a calendar panel.
#     It uses the field.json template to generate the field.

#     Args:
#         location (str): The station name
#         field_name (str): The field name that we want to query

#     Returns:
#         dict: The fields of the panel as it is in field.json
#     """
#     template = env.get_template("field.json")
#     path = f'$[*][stationName.value="{location}"].($count(`{field_name}`) > 0 ? `{field_name}`.value : null)'
#     type = types_resolver.resolve(data_source.query, field_name, data_source.uri)

#     return json.loads(
#         template.render(
#             path=path,
#             language="jsonata",
#             name=field_name,
#             type=type,
#         )
#     )


def generate_fiware_field_extreme_values(
    field_name: str,
    location: str,
    title: str,
) -> dict:
    """Extreme values pannel needs the following data points
    attributes, value, unit
    we are simulating attributes and unit

    Args:
        field_name (str): the field to be extracted
        location (str): location that we filter by
        title (str): the title of the query (attributes | value | unit)

    Returns:
        dict: fields as it is in fields.json
    """
    template = env.get_template("field.json")
    if title == "attribute" or title == "unit":
        path = f'$[*][stationName.value="{location}"].($count(`{field_name}`) > 0 ? "{field_name}" : "{field_name}")'
        type = "string"
    elif title == "value":
        path = f'$[*][stationName.value="{location}"].($count(`{field_name}`) > 0 ? `{field_name}`.value : null)'
        type = "number"

    return json.loads(
        template.render(
            path=path,
            language="jsonata",
            name=title,
            type=type,
        )
    )


def generate_fiware_field(
    location: str,
    field_name: str,
    types_resolver: TypesResolver,
    data_source: Datasource,
) -> dict:
    """This function generates a field for a multiple line panel or a calendar panel.
    It uses the field.json template to generate the field.

    Args:
        location (str): The station name
        field_name (str): The field name that we want to query

    Returns:
        dict: The fields of the panel as it is in field.json
    """
    template = env.get_template("field.json")
    if field_name == "dateObserved":
        path = f'$[*][stationName.value="{location}"].($count(`{field_name}`) > 0 ? $toMillis(`{field_name}`.value) : null)'
    else:
        path = f'$[*][stationName.value="{location}"].($count(`{field_name}`) > 0 ? `{field_name}`.value : null)'
    type = types_resolver.resolve(data_source.query, field_name, data_source.uri)

    return json.loads(
        template.render(
            path=path,
            language="jsonata",
            name=field_name,
            type=type,
        )
    )


def generate_coordiante_field(coordinates: Coordinates) -> dict:
    """This function generates the field for the coordinate of the geomap panel.

    Returns:
        dict: field as it is in field.json
    """
    template = env.get_template("field.json")

    return json.loads(
        template.render(
            path=f'$[*].location.value.coordinates[{coordinates.value["index"]}]',
            language="jsonata",
            name=coordinates.value["name"],
            type="number",
        )
    )



def _generate_field_for_object(
    field_name: str,
    sub_fields: Keys,
    types_resolver: TypesResolver,
    data_source: Datasource,
) -> tuple[list[dict], list | None]:
    """This function is used when the field is an object.
    Object refers to a complex data type like a dict or a list.
    It generates the fields for the sub_fields of the object.

    Args:
        field_name (str): Name of the field/the element that we want to query
        sub_fields (Keys): The subfields of the object

    Returns:
        tuple[list[dict], list | None]: list of fields as it is in field.json,
        list of fields that needs to be concatenated by the transformation
    """
    template = env.get_template("field.json")
    to_return = []  # TODO: change to None, if it always one element, why is it a list?
    group = [field_name]

    for key in sub_fields:
        inner_type = types_resolver.resolve(
            data_source.query, f"{field_name}.{key}", data_source.uri
        )
        path = f"$[*].($count(`{field_name}`.value.`{key}`) > 0 ? `{field_name}`.value.`{key}` : null)"
        to_return.append(
            json.loads(
                template.render(
                    path=path,
                    language="jsonata",
                    name=key,
                    type=inner_type,
                )
            )
        )
        group.append(key)

    return to_return, group


def generate_field(
    field_name: str, types_resolver: TypesResolver, data_source: Datasource
) -> tuple[list[dict], list | None]:
    """This function generated a generic field for the field_name.

    INFO about `path` for `id` field:
    - `id` can also contain `timestamp` or `latest` and we want to remove it
    - Example: Madrid-AirQualityObserved-28079004-2020-05-06T00:00:00
    change to -> Madrid-AirQualityObserved-28079004

    Args:
        field_name (str): The name of the field that we want to query
        types_resolver (TypesResolver): Typeresolver finds the type of the field
        data_source (Datasource): The datasource that we want to query

    Returns:
        tuple[list[dict], list | None]: list of fields as it is in field.json,
        list of fields that needs to be concatenated by the transformation or None
    """
    if field_name == "id":
        path = (
            r'$[*].id.$replace(/-(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}|latest)$/,"")'
        )
    else:
        path = f"$[*].($count(`{field_name}`) > 0 ? `{field_name}`.value : null)"

    template = env.get_template("field.json")
    type = types_resolver.resolve(data_source.query, field_name, data_source.uri)

    if not type:
        type = "auto"

    if isinstance(type, Keys):
        return _generate_field_for_object(field_name, type, types_resolver, data_source)

    return (
        [
            json.loads(
                template.render(
                    path=path,
                    language="jsonata",
                    name=field_name,
                    type=type,
                )
            )
        ],
        None,
    )


def generate_time_field_for_dataskope() -> dict:
    return json.loads(
        env.get_template("field.json").render(
            path="$[*].measurementResults.$toMillis(timeStamp)",
            language="jsonata",
            name="timeStamp",
            type="time",
        )
    )


def generate_value_field_for_dataskope(
    alias: str,
    types_resolver: TypesResolver,
    data_source: Datasource,
) -> dict:
    data_type = types_resolver.resolve_dataskop(
        data_source.uri,
        data_source.config.token,
        data_source.config.measurements[alias],
    )

    return json.loads(
        env.get_template("field.json").render(
            path=f"$[*].measurementResults.${data_type}(value)",
            language="jsonata",
            name="value",
            type=data_type,
        )
    )

def generate_coordinate_field_dataskope(type: str) -> dict:
    return json.loads(
        env.get_template("field.json").render(
            path=f"$.measurementResults.location.$number({type})",
            language="jsonata",
            name=type,
            type="number",
        )
    )