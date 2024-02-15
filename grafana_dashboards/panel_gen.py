"""
This module is used to generate the panels for the Grafana dashboard.
Also contains the function to generate the grid position for the panels.

Returns:
    dict: The fields of the panels as it is in the templates
"""
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from trasformations import concat_fields, group_by, organize
from model import BarChart, Datasource, PieChart, XYChart, TimeSeries, GeoMap, SingleLine, Calendar
from types_resolver import Keys, TypesResolver
from field_generators import generate_field, generate_coordiante_field, generate_time_field_for_single_line, Coordinates


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


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

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            xField=config.traces[0],
            fields=fields,
            transformations=transformations,
            type=data_source.query,
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
            type=data_source.query,
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
            type=data_source.query,
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
            type=data_source.query,
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

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            layerName=data_source.query,
            transformations=transformations,
            fields=fields,
            type=data_source.query,
            title=title,
        )
    )


def generate_single_line(
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
    template = env.get_template("single_line.json")
    fields = []
    transformations = []

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
                f"{name} (last)": name for name in config.traces if name != "dateObserved"
            },
        )
    )

    for name in config.traces:
        if name != "dateObserved":
            y_axis_label = name + " values"

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id),
            id=id,
            fields=fields,
            type=data_source.query,
            title=title,
            transformations=transformations,
            y_axis_label = y_axis_label,
        )
    )

def generate_field_calendar(
    location: str,
    field_name: str,
    types_resolver: TypesResolver,
    data_source: Datasource,
)-> dict:
    """
    Should generate the fields for the calendar panel
    Query example:
    $[*][stationName.value="Escuelas Aguirre"].SO2.value
    $[*][stationName.value="Escuelas Aguirre"].dateObserved.value

    $[*][stationName.value={location}].{field_name}.value
    """
    pass

def generate_target(
    location: str,
    field_name: str,
    types_resolver: TypesResolver,
    data_source: Datasource,
)-> dict:
    """Should generate the targets for the calendar panel
    each group of location-element should have a target
    """
    template = env.get_template("target.json")
    fields = []
    refID = location + "-" + field_name
    
    pass

# locations
# [ "Pza. de España", "Escuelas Aguirre", "Avda. Ramón y Cajal", "Arturo Soria", "Villaverde", 
# "Farolillo", "Casa de Campo", "Barajas Pueblo", "Pza. del Carmen", "Moratalaz", "Cuatro Caminos", 
# "Barrio del Pilar", "Vallecas", "Mendez Alvaro", "Castellana", "Parque del Retiro", "Plaza Castilla", 
# "Ensanche de Vallecas", "Urb. Embajada", "Pza. Fernández Ladreda", "Sanchinarro", "El Pardo", "Juan Carlos I", "Tres Olivos" ]

# elements
# CO, NO, NO2, NOx, SO2, PM2.5, PM10, O3, TOL, BEN, EBE, TCH, CH4, NMHC

def generate_calendar(
    id: int,
    config: Calendar,
    type_resolver: TypesResolver,
    data_source: Datasource,
    title: str,
) -> dict:
    """
    I think here we can separate the targets into location and elements 
    After that combine them into location-element 
    """
    pass