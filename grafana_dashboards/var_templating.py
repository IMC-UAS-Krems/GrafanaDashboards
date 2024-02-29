def create_template_variable(variable_name: str, query: str) -> dict:
    """Creates a template variable for the dashboard.

    Args:
        variable_name: name of the variable
        query: query to be used to get the data for the variable

    Returns:
        template as a dictionary
    """
    return {
        "datasource": {"type": "marcusolsson-json-datasource", "uid": "2RGTUW4Sk"},
        "definition": "",
        "hide": 0,
        "includeAll": False,
        "multi": False,
        "name": variable_name,
        "options": [],
        "query": {
            "cacheDurationSeconds": 300,
            "fields": [
                {
                    "jsonPath": query,
                    "language": "jsonata",
                }
            ],
            "method": "GET",
            "params": [["type", "AirQualityObserved"], ["limit", "1000"]],
            "queryParams": "",
            "urlPath": "",
        },
        "refresh": 1,
        "regex": "",
        "skipUrlSync": False,
        "sort": 0,
        "type": "query",
    }
