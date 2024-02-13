# GrafanaDashboards

## grafana_dashboards

### main.py

Holds the API logic and generates the dashboard JSON file.

### panel_gen.py

Holds the logic for generating the panels. Each panel has its own function.

Panels:

- Barchart - generate_bar_chart()
- Piechart - generate_pie_chart()
- XYChart - generate_xy_chart()
- TimeSeries - generate_time_series() 
- Geomap - generate_geomap()
- Single Line Smartcommunities - generate_single_line()


Other functions:

- generate_grid_pos() - generates the grid position for the panels in the dashboard

### field_generators.py

Because we have multiple functions that generate fields for the panels, we have a separate file for this logic. 

- generate_time_field_for_single_line() - generates the time field for the single line panel 
- generate_coordinate_field() - generates the coordinate field for the geomap panel
- _generate_field_for_object() - generates the field for an object in the panel
- generate_field() - generates a generic field for the panel

### model.py

Holds the model for the dashboard.

**Note**: SingleLine model is implemented for now just to implement the logic for the single line panel. Needs to be changed whith the model from Lucia 

**Note 2**: All models have `traces` for fields to be extracted, only geomap has `data`. Is there a technical reason for this or can we change it to `traces` to be consistent?

