from enum import Enum
import json


from jinja2 import Environment, FileSystemLoader, select_autoescape
from grafana_dashboards.trasformations import concat_fields, group_by, organize
from model import BarChart, Datasource, PieChart, XYChart, TimeSeries, GeoMap
from types_resolver import Keys, TypesResolver


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


class Coordinates(Enum):
    LONGITUDE = {"name": "lon", "index": 0}
    LATITUDE = {"name": "lat", "index": 1}


def generate_coordiante_field(coordinates: Coordinates) -> dict:
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
            path=f'$[*].location.value.coordinates[{coordinates.value["index"]}]',
            name=coordinates.value["name"],
            type="number",
        )
    )


def generate_field_for_object(
    field_name: str,
    sub_fields: Keys,
    types_resolver: TypesResolver,
    data_source: Datasource,
) -> tuple[list[dict], list | None]:
    """This function generates a field for a panel in case the field is an object.

    Args:
        field_name: Name of the field/the element that we want to query
        sub_fields: Inner fields of the `field_name` field (the object)
        types_resolver: From the types_resolver.py file. The field type is resolved using this object
        data_source: From the model.py file. The data source is used to get the type of the query

    Returns:
        tuple: list of fields as it is in field.json (list can contain only one element), list of fields that needs to be concatenated
        by the transformation
    """
    template = env.get_template("field.json")
    to_return = []
    group = [field_name]

    for key in sub_fields:
        inner_type = types_resolver.resolve(
            data_source.query.type, f"{field_name}.{key}", data_source.uri
        )
        path = f"$[*].($count(`{field_name}`.value.`{key}`) > 0 ? `{field_name}`.value.`{key}` : null)"
        to_return.append(
            json.loads(
                template.render(
                    path=path,
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
    """This function generates a field for a panel.
    It uses the field.json template to generate the field.

    Args:
        field_name (str): Name of the field/the element that we want to query
        types_resolver (TypesResolver): From the types_resolver.py file. The field type is resolved using this object
        data_source (Datasource): From the model.py file. The data source is used to get the type of the query

    Returns:
        tuple: list of fields as it is in field.json (list can contain only one element), list of fields that needs to be concatenated by the
        transformation
    """

    # INFO: a little bit hacky, but works for now. It's needed to group the fields that are in the same object.
    # In our case `id` can also conatin `timestamp` or `latest`
    # Example:
    # Madrid-AirQualityObserved-28079004-2020-05-06T00:00:00 -> Madrid-AirQualityObserved-28079004
    if field_name == "id":
        path = r'$[*].id.$replace(/-(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}|latest)$/,"")'  # a bit stupid needs to be resolved in the futur, works for now
    else:
        path = f"$[*].($count(`{field_name}`) > 0 ? `{field_name}`.value : null)"

    template = env.get_template("field.json")
    type = types_resolver.resolve(data_source.query.type, field_name, data_source.uri)

    if not type:
        type = "auto"

    if isinstance(type, Keys):
        return generate_field_for_object(field_name, type, types_resolver, data_source)

    return (
        [
            json.loads(
                template.render(
                    path=path,
                    name=field_name,
                    type=type,
                )
            )
        ],
        None,
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
            x=(col % 2) * 12,
            y=(col // 2) * 8,
        )
    )


def generate_bar_chart(
    id: int,
    config: BarChart,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """This function generates the bar chart panel.

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

        # there are some fields that are in the same object, so we need to group them
        if group:
            transformations.append(concat_fields(group[0], group[1:]))
            # since we want to group inner fields of a key (object) we need to hide them from the user
            transformations.append(organize(exclude_by_name=group[1:]))
            # but keep them for the Grafana since they are needed for transformation (otherwise the grouping will fail)
            extra_data.extend(group[1:])

        fields.extend(generated_fields)

    config.traces.extend(
        extra_data
    )  # add the extra data to the config so we can group them

    transformations.append(group_by("id", config.traces))
    transformations.append(
        organize(
            rename_by_name={
                f"{name} (last)": name for name in config.traces if name != "id"
            },
        )
    )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            xField=config.traces[0],
            fields=fields,
            transformations=transformations,
            type=data_source.query.type,
            title=title,
        )
    )


def generate_pie_chart(
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

    for field_name in config.traces:
        generated_fields, _ = generate_field(field_name, type_resolver, data_source)
        fields.extend(generated_fields)

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            pie_chart_type=config.pie_chart_type,
            fields=fields,
            type=data_source.query.type,
            title=title,
        )
    )


def generate_xy_chart(
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
    fields = []

    for field_name in config.traces:
        generated_fields, _ = generate_field(field_name, type_resolver, data_source)
        fields.extend(generated_fields)

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            fields=fields,
            type=data_source.query.type,
            title=title,
        )
    )


def generate_time_series(
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
    fields = []

    for field_name in config.traces:
        generated_fields, _ = generate_field(field_name, type_resolver, data_source)
        fields.extend(generated_fields)

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            fields=fields,
            type=data_source.query.type,
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
    """This function generates the geomap panel.

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
    fields = []
    transformations = []
    extra_data = []

    if "id" not in config.data:
        config.data.append("id")

    for field_name in config.data:
        if field_name == "location":
            continue

        generated_fields, group = generate_field(field_name, type_resolver, data_source)

        # there are some fields that are in the same object, so we need to group them
        if group:
            transformations.append(concat_fields(group[0], group[1:]))
            # since we want to group inner fields of a key (object) we need to hide them from the user
            transformations.append(organize(exclude_by_name=group[1:]))
            # but keep them for the Grafana since they are needed for transformation (otherwise the grouping will fail)
            extra_data.extend(group[1:])

        fields.extend(generated_fields)

    # call generate coordinate field separately
    fields.append(generate_coordiante_field(Coordinates.LONGITUDE))
    fields.append(generate_coordiante_field(Coordinates.LATITUDE))

    # we need the names of the fields for the group_by
    # NOTE: this can be extracted into separate function (location_group_by) because there can be more than one group_by
    config.data.append(Coordinates.LONGITUDE.value["name"])
    config.data.append(Coordinates.LATITUDE.value["name"])

    config.data.extend(
        extra_data
    )  # add the extra data to the config so we can group them

    transformations.append(group_by("id", config.data))
    transformations.append(
        organize(
            rename_by_name={
                f"{name} (last)": name for name in config.data if name != "id"
            },
        )
    )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            layerName=data_source.query.type,
            transformations=transformations,
            fields=fields,
            type=data_source.query.type,
            title=title,
        )
    )
