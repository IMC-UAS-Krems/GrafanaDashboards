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


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


class Coordinates(Enum):
    LONGITUDE = {"name": "lon", "index": 0}
    LATITUDE = {"name": "lat", "index": 1}


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
