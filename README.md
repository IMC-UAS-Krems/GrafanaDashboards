# GrafanaDashboards

## grafana_dashboards

### main.py

Holds the API logic and generates the dashboard JSON file.

### panel_gen.py

Holds the logic for generating the panels.

Panels:

- Barchart - generate_bar_chart()
- Piechart - generate_pie_chart()
- XYChart - generate_xy_chart()
- TimeSeries - generate_time_series() - has some issues with the time field in types_resolver.py
- Geomap - generate_geomap()
  - has a functipn generate_coordinate_field() because the coordinates are stored in a list in the data

Other functions:

- generate_uid() - needs to be worked on more

### types_resolver.py

Found some issues with the time field in the TimeSeries panel, returns it as "String" instead of "Time" and the time field is not recognized as a time field in the dashboard.

Also types are returned with a capital letter, but the dashboard JSON file needs them with a lowercase letter. Returning them with Capital letter is like you don't return anything.
