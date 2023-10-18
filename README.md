# GrafanaDashboards

## air_quality_templates.json

Added a json template for JSON API data source about air quality.

### Panels

Created panels using the following visualizations:

- Bar Chart Stacked
- Bar Chart
  - Considering the amount of data it is not that visible.
- NO Histogram
  - Serves as a template for creating a histogram based on one component of our data.
- Gauge
- Geomap
  - Not that useful for visualizing the data but it is a nice feature to have and we already had the geolocation data.
- Bar gauge
- Table

### PM2.5

Cannot seem to manage to get the PM2.5 data to show up in the table. Tried different ways of formatting the query but no luck.

- $[*].($count('PM2.5') > 0 ? 'PM2.5'.value : null) gets the values but not the nulls so they are returned in the order that they appear, with no link to its id.

- $[*].($count('PM2\.5' > 0 ? 'PM2\.5'.value : null) tried various ways of escaping the ".". Get "Unsupported escape sequence: \"."" error.

- $[*].{"PM2.5" : $count("PM2.5") != 0 ? "PM2.5".value : null} for each id gives [object Object] in the table. This could be caused by trying to find the data with the quotes around the label.

- Calling the label without the quotes gives the "The literal value 5 cannot be used as a step within a path expression" error.

- Escaping the character here doesn't work either.
