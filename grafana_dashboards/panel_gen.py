"""
This module is used to generate the panels for the Grafana dashboard.
Also contains the function to generate the grid position for the panels.

Returns:
    dict: The fields of the panels as it is in the templates
"""

from enum import Enum
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from grafana_dashboards.trasformations import TransformationBuilder

from grafana_dashboards.model import Datasource
from grafana_dashboards.types_resolver import TypesResolver
from grafana_dashboards.field_generators import (
    generate_time_field_for_dataskope,
    generate_value_field_for_dataskope,
    generate_coordinate_field_dataskope,
    generate_fiware_field_extreme_values,
    generate_fiware_field,
    generate_special_value_field_for_dataskope,
    bar_field
)


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps

transformations_class = TransformationBuilder()


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


def generate_target_dataskop_singleline(
    field_name: str,  # example: "O3"
    index_field: int,  # between 0 and 3
    types_resolver: TypesResolver,
    data_source: Datasource,
    panel_type: str,
    hide: bool = False,
) -> dict:
    dataskop = env.get_template("dataskop.json")
    fields = []

    # because the label of the target is location-attribute we need to connect them
    # in the new version we have pannels which expect dash but others expect underscore
    ref_id = field_name

    fields.append(generate_time_field_for_dataskope())
    fields.append(
        generate_value_field_for_dataskope(field_name, types_resolver, data_source)
    )


    return json.loads(
        dataskop.render(
            datasource_uid=data_source.uid,
            fields=fields,
            hide=hide,
            ref_id=ref_id,
            measurement_id=data_source.config.measurements[field_name],
        )
    )


def generate_target(
    location: str,  # example: "Pza. de España"
    field_name: str,  # example: "O3"
    index_field: int,  # between 0 and 3
    types_resolver: TypesResolver,
    data_source: Datasource,
    panel_type: str,
    hide: bool = False,
) -> dict:
    attributes = ["Temperatur", "Luftfeuchtigkeit", "Feinstaub", "Luftdruck"]
    fiware = env.get_template("fiware.json")
    fields = []

    # because the label of the target is location-attribute we need to connect them
    # in the new version we have pannels which expect dash but others expect underscore
    ref_id = location + "_" + attributes[index_field]

    # also there is a specific order in which the queries need to be called
    # that is why we have so many if statements
    if panel_type == "smartcomm-extremevalues-panel":
        fields.append(
            generate_fiware_field_extreme_values(field_name, location, "attribute")
        )  # ? "NO" : "NO"
        fields.append(
            generate_fiware_field_extreme_values(field_name, location, "value")
        )  # ? `NO`.value : null
        fields.append(
            generate_fiware_field_extreme_values(
                Unit[attributes[index_field]].value, location, "unit"
            )
        )  # ? unit : unit
    else:
        fields.append(
            generate_fiware_field(location, "dateObserved", types_resolver, data_source)
        )
        fields.append(
            generate_fiware_field_extreme_values(field_name, location, "value")
        )

    return json.loads(
        fiware.render(
            ref_id=ref_id,
            fields=fields,
            type=data_source.query,
            hide=hide,
            datasource_uid=data_source.uid,
        )
    )


class Unit(Enum):
    Feinstaub = "µg/m³"
    Luftfeuchtigkeit = "%"
    Temperatur = "°C"
    Luftdruck = "Pa"


def generate_target_mapfhstp_dataskop(
    location: str,  # example: "Pza. de España"
    index_field: int,  # between 0 and 3
    types_resolver: TypesResolver,
    data_source: Datasource,
    panel_type: str,
    hide: bool = False,
) -> dict:
    dataskop = env.get_template("target_mapfhstp.json")

    # because the label of the target is location-attribute we need to connect them
    # in the new version we have pannels which expect dash but others expect underscore
    ref_id = location

    return json.loads(
        dataskop.render(
            datasource_uid=data_source.uid,
            ref_id=ref_id,
            location_id=data_source.config.measurements[location],
        )
    )


