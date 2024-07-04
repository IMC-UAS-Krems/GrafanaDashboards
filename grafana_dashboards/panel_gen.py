"""
This module is used to generate the panels for the Grafana dashboard.
Also contains the function to generate the grid position for the panels.

Returns:
    dict: The fields of the panels as it is in the templates
"""

from enum import Enum
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from grafana_dashboards.trasformations import (
    concat_fields,
    filter_by_value,
    group_by,
    group_by_bar_chart,
    organize,
    merge,
    group_by_geomap,
)
from grafana_dashboards.model import (
    BarChart,
    BarsBubbles,
    BulletGraph,
    DataSourceProvider,
    Datasource,
    ExtremeValues,
    PieChart,
    XYChart,
    TimeSeries,
    GeoMap,
    SingleLine,
    Calendar,
    MultiLine,
    MapFHSTP,
)
from grafana_dashboards.types_resolver import TypesResolver
from grafana_dashboards.field_generators import (
    generate_field,
    generate_time_field_for_dataskope,
    generate_value_field_for_dataskope,
    generate_coordinate_field_dataskope,
    generate_coordiante_field,
    generate_fiware_field_extreme_values,
    generate_fiware_field,
    generate_time_field_for_single_line,
    Coordinates,
)


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


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

    # also there is a specific order in which the queries need to be called
    # that is why we have so many if statements
    # if panel_type == "smartcomm-calendar-panel":
    #     fields.append(
    #         generate_fiware_field(location, field_name, types_resolver, data_source)
    #     )
    #     fields.append(
    #         generate_fiware_field(location, "dateObserved", types_resolver, data_source)
    #     )
    # elif panel_type == "smartcomm-multiplelinechart-panel":
    #     fields.append(
    #         generate_fiware_field(location, "dateObserved", types_resolver, data_source)
    #     )
    #     fields.append(
    #         generate_fiware_field(location, field_name, types_resolver, data_source)
    #     )
    # elif panel_type == "smartcomm-extremevalues-panel":
    #     fields.append(
    #         generate_fiware_field_extreme_values(field_name, location, "attribute")
    #     )  # ? "NO" : "NO"
    #     fields.append(
    #         generate_fiware_field_extreme_values(field_name, location, "value")
    #     )  # ? `NO`.value : null
    #     fields.append(
    #         generate_fiware_field_extreme_values(
    #             Unit[attributes[index_field]].value, location, "unit"
    #         )
    #     )  # ? unit : unit
    # elif panel_type == "smartcomm-bulletgraph-panel":
    #     fields.append(
    #         generate_fiware_field(location, "dateObserved", types_resolver, data_source)
    #     )
    #     fields.append(
    #         generate_fiware_field_extreme_values(field_name, location, "value")
    #     )
    #
    # return json.loads(
    #     template.render(
    #         ref_id=ref_id,
    #         fields=fields,
    #         type=data_source.query,
    #         hide=hide,
    #     )
    # )


def generate_target(
    location: str,  # example: "Pza. de España"
    field_name: str,  # example: "O3"
    index_field: int,  # between 0 and 3
    types_resolver: TypesResolver,
    data_source: Datasource,
    panel_type: str,
    hide: bool = False,
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


def generate_bar_chart_fiware(
    id: int,
    config: BarChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the bar chart panel.

    If the field is an object, we need to group the fields and hide them from the user.
    That is why we have transformations and extra_data.

    Args:
        id (int): The id of the panel
        config (BarChart): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in barchart.json
    """

    template = env.get_template("barchart.json")
    fields = []
    transformations = []
    extra_data = []

    if "id" not in config.traces:
        config.traces.append("id")

    for field_name in config.traces:
        generated_fields, group = generate_field(field_name, type_resolver, data_source)
        if group:
            transformations.append(concat_fields(group[0], group[1:]))
            transformations.append(organize(exclude_by_name=group[1:]))
            extra_data.extend(group[1:])
        fields.extend(generated_fields)

    config.traces.extend(extra_data)

    transformations.append(group_by("id", config.traces))
    transformations.append(
        organize(
            rename_by_name={
                f"{name} (last)": name for name in config.traces if name != "id"
            },
        )
    )

    targets = [
        json.loads(
            env.get_template("fiware.json").render(
                ref_id="A",
                fields=fields,
                type=data_source.query,
                hide=False,
                datasource_uid=data_source.uid,
            )
        )
    ]

    return json.loads(
        template.render(
            datasource_uid=data_source.uid,
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            xField=config.traces[0],
            targets=targets,
            transformations=transformations,
            title=title,
        )
    )


def generate_bar_chart_dataskop(
    id: int,
    config: BarChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the bar chart panel.

    If the field is an object, we need to group the fields and hide them from the user.
    That is why we have transformations and extra_data.

    Args:
        id (int): The id of the panel
        config (BarChart): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in barchart.json
    """

    template = env.get_template("barchart.json")
    targets = []
    transformations = []

    for i, field_name in enumerate(config.traces):
        targets.append(
            generate_target_dataskop(
                field_name,
                index_field=i,
                types_resolver=type_resolver,
                data_source=data_source,
                panel_type=config.type,
                hide=False,
                special_value=True,
                bar=True,
                is_fhstp=False,
            )
        )

    transformations.append(merge())
    # transformations.append(group_by("Fields", config.traces))
    transformations.append(group_by_bar_chart("Fields", config.traces))

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            xField="Fields",
            transformations=transformations,
            title=title,
            targets=targets,
            datasource_uid=data_source.uid,
            measurement_id=data_source.config.measurements[config.traces[0]],
        )
    )


def generate_bar_chart(
    id: int,
    config: BarChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    if data_source.provider == DataSourceProvider.Fiware:
        return generate_bar_chart_fiware(id, config, type_resolver, data_source, title)
    elif data_source.provider == DataSourceProvider.Dataskop:
        return generate_bar_chart_dataskop(
            id, config, type_resolver, data_source, title
        )


def generate_pie_chart_fiware(
    id: int,
    config: PieChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the pie chart panel.

    Args:
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
    fields = []
    transformations = []

    for field_name in config.traces:
        generated_fields, _ = generate_field(field_name, type_resolver, data_source)
        fields.extend(generated_fields)

    transformations.append(filter_by_value("$id_filter", "id"))

    targets = [
        json.loads(
            env.get_template("fiware.json").render(
                ref_id="A",
                fields=fields,
                type=data_source.query,
                hide=False,
                datasource_uid=data_source.uid,
            )
        )
    ]

    return json.loads(
        template.render(
            datasource_uid=data_source.uid,
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            pie_chart_type=config.pie_chart_type,
            targets=targets,
            title=title,
            transformations=transformations,
        )
    )


def generate_pie_chart_dataskop(
    id: int,
    config: PieChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the pie chart panel.

    Args:
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
    targets = []
    transformations = []

    for i, field_name in enumerate(config.traces):
        targets.append(
            generate_target_dataskop(
                field_name,
                index_field=i,
                types_resolver=type_resolver,
                data_source=data_source,
                panel_type=config.type,
                hide=False,
                is_fhstp=False,
            )
        )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            pie_chart_type=config.pie_chart_type,
            title=title,
            transformations=transformations,
            targets=targets,
            datasource_uid=data_source.uid,
        )
    )


def generate_pie_chart(
    id: int,
    config: PieChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    if data_source.provider == DataSourceProvider.Fiware:
        return generate_pie_chart_fiware(id, config, type_resolver, data_source, title)
    elif data_source.provider == DataSourceProvider.Dataskop:
        return generate_pie_chart_dataskop(
            id, config, type_resolver, data_source, title
        )


def generate_xy_chart_dataskop(
    id: int,
    config: XYChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    template = env.get_template("xy.json")
    targets = []
    transformations = []

    for i, field_name in enumerate(config.traces):
        targets.append(
            generate_target_dataskop(
                field_name,
                index_field=i,
                types_resolver=type_resolver,
                data_source=data_source,
                panel_type=config.type,
                hide=False,
                special_value=True,
                is_fhstp=False,
            )
        )

    transformations.append(merge())

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            type=data_source.query,
            title=title,
            transformations=transformations,
            targets=targets,
            measurement_id=data_source.config.measurements[config.traces[0]],
            datasource_uid=data_source.uid,
        )
    )


def generate_xy_chart_fireware(
    id: int,
    config: XYChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the xy chart panel.

    Args:
        id (int): Id of the panel
        config (XYChart): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in xy.json
    """
    template = env.get_template("xy.json")
    fiware_template = env.get_template("fiware.json")
    fields = []
    transformations = []

    for field_name in config.traces:
        generated_fields, _ = generate_field(field_name, type_resolver, data_source)
        fields.extend(generated_fields)

    fiware_template = json.loads(
        fiware_template.render(
            datasource_uid=data_source.uid,
            fields=fields,
            type=data_source.query,
            hide=False,
            ref_id="A",
        )
    )

    transformations.append(filter_by_value("$id_filter", "id"))
    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=[fiware_template],
            title=title,
            transformations=transformations,
            datasource_uid=data_source.uid,
        )
    )


def generate_xy_chart(
    id: int,
    config: XYChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    if data_source.provider == DataSourceProvider.Fiware:
        return generate_xy_chart_fireware(id, config, type_resolver, data_source, title)
    elif data_source.provider == DataSourceProvider.Dataskop:
        return generate_xy_chart_dataskop(id, config, type_resolver, data_source, title)


def generate_time_series_fiware(
    id: int,
    config: TimeSeries,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the time series panel.

    Args:
        id (int): Id of the panel
        config (TimeSeries): The type of the panel
        type_resolver (TypesResolver): Used to generate the field. ! does not work for time
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in timeseries.json
    """
    template = env.get_template("timeseries.json")
    fiware_template = env.get_template("fiware.json")
    fields = []
    transformations = []

    for field_name in config.traces:
        generated_fields, _ = generate_field(field_name, type_resolver, data_source)
        fields.extend(generated_fields)

    transformations.append(filter_by_value("$id_filter", "id"))

    fiware_template = json.loads(
        fiware_template.render(
            datasource_uid=data_source.uid,
            fields=fields,
            type=data_source.query,
            hide=False,
            ref_id="A",
        )
    )

    return json.loads(
        template.render(
            datasource_uid=data_source.uid,
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=[fiware_template],
            title=title,
            transformations=transformations,
        )
    )


def generate_time_series_dataskop(
    id: int,
    config: TimeSeries,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the time series panel.

    Args:
        id (int): Id of the panel
        config (TimeSeries): The type of the panel
        type_resolver (TypesResolver): Used to generate the field. ! does not work for time
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in timeseries.json
    """
    template = env.get_template("timeseries.json")
    targets = []
    transformations = []

    for i, field_name in enumerate(config.traces):
        targets.append(
            generate_target_dataskop(
                field_name,
                index_field=i,
                types_resolver=type_resolver,
                data_source=data_source,
                panel_type=config.type,
                hide=False,
                is_fhstp=False,
            )
        )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            type=data_source.query,
            title=title,
            transformations=transformations,
            targets=targets,
            measurement_id=data_source.config.measurements[config.traces[0]],
            datasource_uid=data_source.uid,
        )
    )


def generate_time_series(
    id: int,
    config: TimeSeries,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    if data_source.provider == DataSourceProvider.Fiware:
        return generate_time_series_fiware(
            id, config, type_resolver, data_source, title
        )
    elif data_source.provider == DataSourceProvider.Dataskop:
        return generate_time_series_dataskop(
            id, config, type_resolver, data_source, title
        )


def generate_geomap_dataskop(
    id: int,
    config: GeoMap,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    template = env.get_template("geomap.json")
    targets = []
    transformations = []

    for i, field_name in enumerate(config.data):
        targets.append(
            generate_target_dataskop(
                field_name,
                index_field=i,
                types_resolver=type_resolver,
                data_source=data_source,
                panel_type=config.type,
                hide=False,
                geomap=True,
                special_value=True,
                is_fhstp=False,
            )
        )

    transformations.append(merge())
    transformations.append(group_by_geomap(["longitude", "latitude"], config.data))

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            layerName=data_source.query,
            transformations=transformations,
            title=title,
            targets=targets,
            datasource_uid=data_source.uid,
        )
    )


def generate_geomap_fiware(
    id: int,
    config: GeoMap,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the geomap panel.

    If the field is an object, we need to group the fields and hide them from the user.
    That is why we have transformations and extra_data.

    We also need to generate the fields for the coordinates separately.

    Args:
        id (int): Id of the panel
        config (GeoMap): The type of the panel
        type_resolver (TypesResolver): Used to generate the field
        data_source (Datasource): Used to generate the field
        title (str): The title of the panel

    Returns:
        dict: The fields of the panel as it is in geomap.json
    """
    template = env.get_template("geomap.json")
    fiware_template = env.get_template("fiware.json")
    fields = []
    transformations = []
    extra_data = []

    if "id" not in config.data:
        config.data.append("id")

    for field_name in config.data:
        if field_name == "location":
            continue
        generated_fields, group = generate_field(field_name, type_resolver, data_source)
        if group:
            transformations.append(concat_fields(group[0], group[1:]))
            transformations.append(organize(exclude_by_name=group[1:]))
            extra_data.extend(group[1:])
        fields.extend(generated_fields)

    fields.append(generate_coordiante_field(Coordinates.LONGITUDE))
    fields.append(generate_coordiante_field(Coordinates.LATITUDE))

    # NOTE: this can be extracted into separate function (location_group_by) because there can be more than one group_by
    config.data.append(Coordinates.LONGITUDE.value["name"])
    config.data.append(Coordinates.LATITUDE.value["name"])

    config.data.extend(extra_data)

    transformations.append(group_by("id", config.data))
    transformations.append(
        organize(
            rename_by_name={
                f"{name} (last)": name for name in config.data if name != "id"
            },
        )
    )

    fiware_template = json.loads(
        fiware_template.render(
            datasource_uid=data_source.uid,
            fields=fields,
            type=data_source.query,
            hide=False,
            ref_id="A",
        )
    )

    return json.loads(
        template.render(
            datasource_uid=data_source.uid,
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=[fiware_template],
            transformations=transformations,
            title=title,
        )
    )


def generate_geomap(
    id: int,
    config: GeoMap,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    if data_source.provider == DataSourceProvider.Fiware:
        return generate_geomap_fiware(id, config, type_resolver, data_source, title)
    elif data_source.provider == DataSourceProvider.Dataskop:
        return generate_geomap_dataskop(id, config, type_resolver, data_source, title)


def generate_single_line_fiware(
    id: int,
    config: SingleLine,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the single line panel for the plugin smartcomm-simpleline-panel.
    Needed to create a separate function for field generation
    The time field can be extracted only with jsonpath language.
    This pannel does not care about location or id fields.
    If this is something we care about needs to be changed.

    Considered only the case when there is one value asked to be displayed on the y axis.

    Returns:
        dict: The fields of the panel as it is in single_line.json
    """
    fiware = env.get_template("fiware.json")
    single_line = env.get_template("single_line.json")

    fields = []
    transformations = []
    targets = []

    for field_name in config.traces:
        if field_name == "dateObserved":
            fields.append(generate_time_field_for_single_line(field_name))
        else:
            generated_fields, _ = generate_field(field_name, type_resolver, data_source)
            fields.extend(generated_fields)

    transformations.append(group_by("dateObserved", config.traces))
    transformations.append(
        organize(
            rename_by_name={
                f"{name} (last)": name
                for name in config.traces
                if name != "dateObserved"
            },
        )
    )

    for name in config.traces:
        if name != "dateObserved":
            y_axis_label = name + " values"

    targets.append(
        json.loads(
            fiware.render(
                ref_id="A",
                fields=fields,
                type=data_source.query,
                hide=False,
                datasource_uid=data_source.uid,
            )
        )
    )

    return json.loads(
        single_line.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            title=title,
            targets=targets,
            transformations=transformations,
            y_axis_label=y_axis_label,
            datasource_uid=data_source.uid,
        )
    )


def generate_single_line_dataskop(
    id: int,
    config: SingleLine,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the single line panel for the plugin smartcomm-simpleline-panel.
    Needed to create a separate function for field generation
    The time field can be extracted only with jsonpath language.
    This pannel does not care about location or id fields.
    If this is something we care about needs to be changed.

    Considered only the case when there is one value asked to be displayed on the y axis.

    Returns:
        dict: The fields of the panel as it is in single_line.json
    """
    single_line = env.get_template("single_line.json")

    transformations = []
    targets = []

    for i, field_name in enumerate(config.traces):
        targets.append(
            generate_target_dataskop(
                field_name,
                index_field=i,
                types_resolver=type_resolver,
                data_source=data_source,
                panel_type=config.type,
                hide=False,
                is_fhstp=False,
            )
        )

    return json.loads(
        single_line.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            title=title,
            targets=targets,
            transformations=transformations,
            y_axis_label=config.traces[0],
            datasource_uid=data_source.uid,
        )
    )


def generate_single_line(
    id: int,
    config: SingleLine,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    if data_source.provider == DataSourceProvider.Fiware:
        return generate_single_line_fiware(
            id, config, type_resolver, data_source, title
        )
    elif data_source.provider == DataSourceProvider.Dataskop:
        return generate_single_line_dataskop(
            id, config, type_resolver, data_source, title
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


def generate_calendar(
    id: int,
    config: Calendar,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the calendar panel.
    I assumed that traces is structured like this:
    locations, dateObserved, elements
    Locations are a max of 8/10
    Elements are a max of 4

    Args:
        config (Calendar): Needs to be introduced also in the definition

    Returns:
        dict: The fields of the panel as it is in calendar.json
    """
    template = env.get_template("calendar.json")
    targets = []

    locations = config.locations
    if "dateObserved" in config.traces:
        config.traces.remove("dateObserved")
    elements = config.traces

    for location in locations:
        for element in elements:
            index_field = elements.index(element)
            if data_source.provider == DataSourceProvider.Dataskop:
                targets.append(
                    generate_target_dataskop(
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                        location=location,
                    )
                )
            else:
                targets.append(
                    generate_target(
                        location,
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                    )
                )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
            datasource_uid=data_source.uid,
        )
    )


def generate_extreme_values(
    id: int,
    config: ExtremeValues,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """Same as Calendar and Multiline this pannel needs the following attributes
    location and elements (we don't need dateObserved)

    Returns:
        dict: The fields in the pannel as it is in extreme_values.json
    """
    template = env.get_template("extreme_values.json")
    targets = []

    locations = config.locations
    if "dateObserved" in config.traces:
        config.traces.remove("dateObserved")
    elements = config.traces

    for location in locations:
        for element in elements:
            index_field = elements.index(element)

            if data_source.provider == DataSourceProvider.Dataskop:
                targets.append(
                    generate_target_dataskop(
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                        location=location,
                    )
                )
            else:
                targets.append(
                    generate_target(
                        location,
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                    )
                )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
            datasource_uid=data_source.uid,
        )
    )


def generate_multiline(
    id: int,
    config: MultiLine,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the multiline panel.
    I assumed that traces is structured like in the calendar panel
    locations, dateObserved, elements
    elements are a max of 4
    locations cannot have any special characters because the plugin does not accept them.

    Returns:
        dict: The fields of the panel as it is in multiline.json
    """
    template = env.get_template("multiline.json")
    targets = []

    locations = config.locations
    if "dateObserved" in config.traces:
        config.traces.remove("dateObserved")
    elements = config.traces

    for location in locations:
        for element in elements:
            index_field = elements.index(element)

            if data_source.provider == DataSourceProvider.Dataskop:
                targets.append(
                    generate_target_dataskop(
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                        location=location,
                        is_fhstp=False,
                    )
                )
            else:
                targets.append(
                    generate_target(
                        location,
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                    )
                )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
            datasource_uid=data_source.uid,
        )
    )


def generate_bullet_graph(
    id: int,
    config: BulletGraph,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the bullet graph panel.
    Each group of queries location-element is a target.
    This is created by target function.
    Bullet graph pannel has a bug
    The panel does not work with more than 11 groups
    That is why we hide one target
    There is also a max of 3 locations and 4 elements that can be displayed

    Args:
        id (int): id of the panel
        config (BulletGraph): definition of the panel
        type_resolver (TypesResolver): resolver for the types
        data_source (Datasource): source of the data
        title (str): title of the panel

    Returns:
        dict: The fields of the panel as it is in bulletpanel.json
    """
    template = env.get_template("bulletpanel.json")
    targets = []

    locations = config.locations
    if "dateObserved" in config.traces:
        config.traces.remove("dateObserved")
    elements = config.traces

    for location in locations:
        for element in elements:
            index_field = elements.index(element)
            hide = elements.index(element) == 0 and locations.index(location) == 0

            if data_source.provider == DataSourceProvider.Dataskop:
                targets.append(
                    generate_target_dataskop(
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                        hide=hide,
                        location=location,
                    )
                )
            else:
                targets.append(
                    generate_target(
                        location,
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                        hide=hide,
                    )
                )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
            datasource_uid=data_source.uid,
        )
    )


def generate_fhstp_map(
    id: int,
    config: MapFHSTP,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the bullet graph panel.
    Each group of queries location-element is a target.
    This is created by target function.
    Bullet graph pannel has a bug
    The panel does not work with more than 11 groups
    That is why we hide one target
    There is also a max of 3 locations and 4 elements that can be displayed

    Args:
        id (int): id of the panel
        config (BulletGraph): definition of the panel
        type_resolver (TypesResolver): resolver for the types
        data_source (Datasource): source of the data
        title (str): title of the panel

    Returns:
        dict: The fields of the panel as it is in bulletpanel.json
    """
    template = env.get_template("map_fhstp.json")
    targets = []

    if "dateObserved" in config.traces:
        config.traces.remove("dateObserved")

    locations = config.traces

    for location in locations:
        index_field = locations.index(location)

        if data_source.provider == DataSourceProvider.Dataskop:
            targets.append(
                generate_target_mapfhstp_dataskop(
                    location,
                    index_field,
                    type_resolver,
                    data_source,
                    config.type,
                )
            )
        else:
            raise Exception("Only Dataskop is supported for this panel")
            targets.append(
                generate_target(
                    location,
                    location,
                    index_field,
                    type_resolver,
                    data_source,
                    config.type,
                    hide=False,
                )
            )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
            datasource_uid=data_source.uid,
        )
    )


def generate_bars_and_bubbles(
    id: int,
    config: BarsBubbles,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the bullet graph panel.
    Each group of queries location-element is a target.
    This is created by target function.
    Bullet graph pannel has a bug
    The panel does not work with more than 11 groups
    That is why we hide one target
    There is also a max of 3 locations and 4 elements that can be displayed

    Args:
        id (int): id of the panel
        config (BulletGraph): definition of the panel
        type_resolver (TypesResolver): resolver for the types
        data_source (Datasource): source of the data
        title (str): title of the panel

    Returns:
        dict: The fields of the panel as it is in bulletpanel.json
    """
    template = env.get_template("bars_bubbles.json")
    targets = []

    locations = config.locations
    if "dateObserved" in config.traces:
        config.traces.remove("dateObserved")
    elements = config.traces

    for location in locations:
        for element in elements:
            index_field = elements.index(element)
            hide = elements.index(element) == 0 and locations.index(location) == 0

            if data_source.provider == DataSourceProvider.Dataskop:
                targets.append(
                    generate_target_dataskop(
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                        hide=hide,
                        location=location,
                    )
                )
            else:
                targets.append(
                    generate_target(
                        location,
                        element,
                        index_field,
                        type_resolver,
                        data_source,
                        config.type,
                        hide=hide,
                    )
                )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
            datasource_uid=data_source.uid,
        )
    )
