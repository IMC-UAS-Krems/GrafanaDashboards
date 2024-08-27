from enum import Enum
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from grafana_dashboards.trasformations import TransformationBuilder

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
    generate_target_dataskop,
    generate_grid_pos,
    Coordinates,
)

from grafana_dashboards.panel_gen import generate_target, generate_target_mapfhstp_dataskop, generate_target_dataskop_singleline


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps

transformations_class = TransformationBuilder()

class DataskopeBuilder:
    @staticmethod
    def generate_bar_chart(
        id: int,
        config: BarChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/barchart.json")
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

        transformations.append(transformations_class.merge())
        transformations.append(transformations_class.group_by_bar_chart("Fields", config.traces))

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
    
    @staticmethod
    def generate_pie_chart(
        id: int,
        config: PieChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/piechart.json")
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
    
    @staticmethod
    def generate_xy_chart(
        id: int,
        config: XYChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/xy.json")
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

        transformations.append(transformations_class.merge())

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
    
    @staticmethod
    def generate_time_series(
        id: int,
        config: TimeSeries,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/timeseries.json")
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
    
    @staticmethod
    def generate_geo_map(
        id: int,
        config: GeoMap,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/geomap.json")
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

        transformations.append(transformations_class.merge())
        transformations.append(transformations_class.group_by_geomap(["longitude", "latitude"], config.data))

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
    
    @staticmethod
    def generate_single_line(
        id: int,
        config: SingleLine,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        single_line = env.get_template("fhsp/single_line.json")

        transformations = []
        targets = []

        for i, field_name in enumerate(config.traces):
            targets.append(
                generate_target_dataskop_singleline(
                    field_name,
                    index_field=i,
                    types_resolver=type_resolver,
                    data_source=data_source,
                    panel_type=config.type,
                    hide=False,
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

class FirewareBuilder:
    @staticmethod
    def generate_bar_chart(
        id: int,
        config: BarChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/barchart.json")
        fields = []
        transformations = []
        extra_data = []

        if "id" not in config.traces:
            config.traces.append("id")

        for field_name in config.traces:
            generated_fields, group = generate_field(field_name, type_resolver, data_source)
            if group:
                transformations.append(transformations_class.concat_fields(group[0], group[1:]))
                transformations.append(transformations_class.organize(exclude_by_name=group[1:]))
                extra_data.extend(group[1:])
            fields.extend(generated_fields)

        config.traces.extend(extra_data)

        transformations.append(transformations_class.group_by("id", config.traces))
        transformations.append(
            transformations_class.organize(
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
    
    @staticmethod
    def generate_pie_chart(
        id: int,
        config: PieChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/piechart.json")
        fields = []
        transformations = []

        for field_name in config.traces:
            generated_fields, _ = generate_field(field_name, type_resolver, data_source)
            fields.extend(generated_fields)

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
    
    @staticmethod
    def generate_xy_chart(
        id: int,
        config: XYChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/xy.json")
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
    
    @staticmethod
    def generate_time_series(
        id: int,
        config: TimeSeries,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/timeseries.json")
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
    
    @staticmethod
    def generate_geo_map(
        id: int,
        config: GeoMap,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("grafana/geomap.json")
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
                transformations.append(transformations_class.concat_fields(group[0], group[1:]))
                transformations.append(transformations_class.organize(exclude_by_name=group[1:]))
                extra_data.extend(group[1:])
            fields.extend(generated_fields)

        fields.append(generate_coordiante_field(Coordinates.LONGITUDE))
        fields.append(generate_coordiante_field(Coordinates.LATITUDE))

        # NOTE: this can be extracted into separate function (location_group_by) because there can be more than one group_by
        config.data.append(Coordinates.LONGITUDE.value["name"])
        config.data.append(Coordinates.LATITUDE.value["name"])

        config.data.extend(extra_data)

        transformations.append(transformations_class.group_by("id", config.data))
        transformations.append(
            transformations_class.organize(
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
    
    @staticmethod
    def generate_single_line(
        id: int,
        config: SingleLine,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        fiware = env.get_template("fiware.json")
        single_line = env.get_template("fhsp/single_line.json")

        fields = []
        transformations = []
        targets = []

        for field_name in config.traces:
            if field_name == "dateObserved":
                fields.append(generate_time_field_for_single_line(field_name))
            else:
                generated_fields, _ = generate_field(field_name, type_resolver, data_source)
                fields.extend(generated_fields)

        transformations.append(transformations_class.group_by("dateObserved", config.traces))
        transformations.append(
            transformations_class.organize(
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


class PanelBuilder:
    @staticmethod
    def generate_bar_chart(
        id: int,
        config: BarChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        if data_source.provider == DataSourceProvider.Fiware:
            return FirewareBuilder.generate_bar_chart(id, config, type_resolver, data_source, title)
        elif data_source.provider == DataSourceProvider.Dataskop:
            return DataskopeBuilder.generate_bar_chart(
                id, config, type_resolver, data_source, title
            )

    @staticmethod
    def generate_pie_chart(
        id: int,
        config: PieChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        if data_source.provider == DataSourceProvider.Fiware:
            return FirewareBuilder.generate_pie_chart(id, config, type_resolver, data_source, title)
        elif data_source.provider == DataSourceProvider.Dataskop:
            return DataskopeBuilder.generate_pie_chart(
                id, config, type_resolver, data_source, title
            )

    @staticmethod
    def generate_xy_chart(
        id: int,
        config: XYChart,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        if data_source.provider == DataSourceProvider.Fiware:
            return FirewareBuilder.generate_xy_chart(id, config, type_resolver, data_source, title)
        elif data_source.provider == DataSourceProvider.Dataskop:
            return DataskopeBuilder.generate_xy_chart(id, config, type_resolver, data_source, title)

    @staticmethod
    def generate_time_series(
        id: int,
        config: TimeSeries,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        if data_source.provider == DataSourceProvider.Fiware:
            return FirewareBuilder.generate_time_series(
                id, config, type_resolver, data_source, title
                )
        elif data_source.provider == DataSourceProvider.Dataskop:
            return DataskopeBuilder.generate_time_series(
                id, config, type_resolver, data_source, title
            )

    @staticmethod
    def generate_geo_map(
        id: int,
        config: GeoMap,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        if data_source.provider == DataSourceProvider.Fiware:
            return FirewareBuilder.generate_geo_map(id, config, type_resolver, data_source, title)
        elif data_source.provider == DataSourceProvider.Dataskop:
            return DataskopeBuilder.generate_geo_map(
                id, config, type_resolver, data_source, title
            )

    @staticmethod
    def generate_single_line(
        id: int,
        config: SingleLine,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        if data_source.provider == DataSourceProvider.Fiware:
            return FirewareBuilder.generate_single_line(
                id, config, type_resolver, data_source, title
            )
        elif data_source.provider == DataSourceProvider.Dataskop:
            return DataskopeBuilder.generate_single_line(
                id, config, type_resolver, data_source, title
            )

    @staticmethod
    def generate_calendar(
        id: int,
        config: Calendar,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("fhsp/calendar.json")
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

    @staticmethod
    def generate_extreme_values(
        id: int,
        config: ExtremeValues,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("fhsp/extreme_values.json")
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

    @staticmethod
    def generate_multi_line(
        id: int,
        config: MultiLine,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("fhsp/multiline.json")
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

    @staticmethod
    def generate_bullet_graph(
        id: int,
        config: BulletGraph,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("fhsp/bulletpanel.json")
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

    @staticmethod
    def generate_fhsp_map(
        id: int,
        config: MapFHSTP,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("fhsp/map_fhstp.json")
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

    @staticmethod
    def generate_bars_and_bubbles(
        id: int,
        config: BarsBubbles,
        type_resolver: TypesResolver,
        data_source: Datasource,
        title: str,
    ) -> dict:
        template = env.get_template("fhsp/bars_bubbles.json")
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