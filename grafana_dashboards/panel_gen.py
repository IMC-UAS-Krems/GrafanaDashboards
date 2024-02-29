"""
This module is used to generate the panels for the Grafana dashboard.
Also contains the function to generate the grid position for the panels.

Returns:
    dict: The fields of the panels as it is in the templates
"""
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from trasformations import concat_fields, group_by, organize
from model import BarChart, Datasource, PieChart, XYChart, TimeSeries, GeoMap, SingleLine, Calendar, MultiLine, ExtremeValues
from types_resolver import TypesResolver
from field_generators import generate_field, generate_coordiante_field, generate_field_multiline_and_calendar, generate_time_field_for_single_line, Coordinates


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps


def generate_grid_pos(col: int, panel_type:str) -> dict:
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
            grid_pos=generate_grid_pos(id, config.type),
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
            grid_pos=generate_grid_pos(id, config.type),
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
            grid_pos=generate_grid_pos(id, config.type),
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
            grid_pos=generate_grid_pos(id, config.type),
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
            grid_pos=generate_grid_pos(id, config.type),
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
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            fields=fields,
            type=data_source.query,
            title=title,
            transformations=transformations,
            y_axis_label = y_axis_label,
        )
    )

def generate_field_extreme_values(
    field_name: str,
    location: str, 
    title:str,
)-> dict:
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
            path= path,
            language="jsonata",
            name= title,
            type=type,
        )
    )


def generate_target(
    location: str, # example: "Pza. de España"
    field_name: str, # example: "O3"
    index_field: int, # between 0 and 3
    types_resolver: TypesResolver,
    data_source: Datasource,
    panel_type: str,
)-> dict:
    """This function generates the target for the calendar panel.
    Each target is a query for a specific location and a specific field.
    Currently the plugin accepts only 4 fields: "Luftfeuchtigkeit", "Temperatur", "Feinstaub", "Luftdruck"
    Because we cannot have our own attributes we mask them with the ones that are available in the plugin.

    Args:
        location (str): The station name
        field_name (str): The field name that we want to query
        index_field (int): The index of the field 
        data_source (Datasource): Used to generate the field and the type of the query

    Returns:
        dict: The fields of the panel as it is in target.json
    """
    attributes = ["Luftfeuchtigkeit", "Temperatur", "Feinstaub", "Luftdruck"]
    template = env.get_template("target.json")
    fields = []
    ref_id = location + "-" + attributes[index_field]

    if panel_type == "smartcomm-calendar-panel":
        fields.append(generate_field_multiline_and_calendar(location, field_name, types_resolver, data_source))
        fields.append(generate_field_multiline_and_calendar(location, "dateObserved", types_resolver, data_source))
    elif panel_type == "smartcomm-multiplelinechart-panel":
        fields.append(generate_field_multiline_and_calendar(location, "dateObserved", types_resolver, data_source))
        fields.append(generate_field_multiline_and_calendar(location, field_name, types_resolver, data_source))
    elif panel_type == "smartcomm-extremevalues-panel":
        if attributes[index_field] == "Feinstaub":
            unit = "µg/m³"
        elif attributes[index_field] == "Luftfeuchtigkeit":
            unit = "%"
        elif attributes[index_field] == "Temperatur":
            unit = "°C"
        elif attributes[index_field] == "Luftdruck":
            unit = "Pa"

        # attribute
        fields.append(generate_field_extreme_values(field_name, location, "attribute", types_resolver, data_source)) #? "NO" : "NO"
        # value
        fields.append(generate_field_extreme_values(field_name, location, "value", types_resolver, data_source)) # ? `NO`.value : null
        # unit
        fields.append(generate_field_extreme_values(unit, location, "unit", types_resolver, data_source)) # ? unit : unit

    return json.loads(
        template.render(
            ref_id=ref_id,
            fields=fields,
            type=data_source.query,
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
    locations = []

    for location in config.traces:
        if location == "dateObserved":
            break
        locations.append(location)

    elements = config.traces[len(locations)+1:]

    for location in locations:
        for element in elements:
            index_field = elements.index(element)
            targets.append(
                generate_target(location, element, index_field, type_resolver, data_source, config.type)
            )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
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
    templates = []
    locations = []

    for location in config.traces:
        if location == "dateObserved":
            break
        locations.append(location)

    elements = config.traces[len(locations)+1:]

    for location in locations:
        for element in elements:
            index_field = elements.index(element)
            templates.append(
                generate_target(location, element, index_field, type_resolver, data_source, config.type)
            )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=templates,
            type=data_source.query,
            title=title,
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
    locations = []

    for location in config.traces:
        if location == "dateObserved":
            break
        locations.append(location)

    elements = config.traces[len(locations)+1:]

    for location in locations:
        for element in elements:
            index_field = elements.index(element)
            targets.append(
                generate_target(location, element, index_field, type_resolver, data_source, config.type)
            )

    return json.loads(
        template.render(
            grid_pos=generate_grid_pos(id, config.type),
            id=id,
            targets=targets,
            type=data_source.query,
            title=title,
        )
    )
