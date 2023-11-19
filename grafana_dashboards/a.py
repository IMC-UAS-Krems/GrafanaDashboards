from model import Config

my = {
  "service": {
    "title": "Grafana dashboad",
    "scope": "Environment",
    "version": {
      "major": 1,
      "minor": 0,
      "patch": 0
    }
  },
  "data_sources": {
    "datasource1": {
      "provider": "Fiware",
      "type": "SmartMeter",
      "uri": "https://data.iiss.at/dataskop/fiwarenosec",
      "query": {
        "type": "AirQualityObserved"
      }
    }
  },
  "application": {
    "type": "Web",
    "layout": "SinglePage",
    "roles": ["User", "Superuser", "Admin"],
    "panels": {
        "Pie chart": {
            "type": "pie_chart",
            "source": "datasource1",
            "traces": ["NOx", "O3", "NO2", "SO2"],
            "pie_chart_type": "pie",
        },
        "Time Series": {
            "type": "timeseries",
            "source": "datasource1",
            "traces": ["dateObserved", "NOx", "O3", "NO2", "SO2"]
        },
        "Bar chart": {
            "type": "bar_chart",
            "source": "datasource1",
            "traces": ["stationCode", "NOx", "O3", "NO2", "SO2"]
        },
        "Map": {
            "type": "geomap",
            "source": "datasource1",
            "data": ["location", "stationName", "O3", "NO2", "SO2"],
            "area": "Vienna"
        },
        "XY chart": {
            "type": "xy_chart",
            "source": "datasource1",
            "traces": ["dateObserved", "NOx", "O3", "NO2", "SO2"]
        }
    }
  },
  "deployment": {
    "additionalProp1": {
      "additionalProp1": {
        "uri": "string",
        "port": 0,
        "type": "string"
      }
     
    }
  }
}

config = Config(**my)