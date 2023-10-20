from typing import Literal, TypeAlias
from enum import Enum

from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import requests

Type: TypeAlias = Literal["Number", "String", "Time", "Boolean"]

class Keys(list):
    pass

class List(Enum):
    Number = "Number"
    String = "String"
    Time = "Time"
    Boolean = "Boolean"



class TypesResolver:
    """
    This class is used to resolve the type of a given path in a given type or data source

    >>> with TypesResolver() as tr:
    >>>     tr.resolve("fiware_model_type", "path", "url")
    """

    def __init__(self) -> None:
        self._spec_cache = {}
        self._data_cache = {}
        self._urls = {
            "AirQualityObserved": "https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/38ab75f0c13b2a838a45241132165cbefe448ca6/AirQualityObserved/model.yaml",
            "PointOfInterest": "https://raw.githubusercontent.com/smart-data-models/dataModel.PointOfInterest/d093271220bdd173d31b3388f0b00953ebbdc0cd/PointOfInterest/model.yaml",
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear_cache()

    def clear_cache(self):
        self._spec_cache = {}
        self._data_cache = {}

    def resolve(self, type: str, path: str, data_source_url: str) -> List | Keys | Type | None:
        """
        Tries to resolve the type of a given path in a given type or data source. First, it tries to resolve a type from the model, if it fails, it tries to resolve it from the first item in the data source

        Returns `None` if the path could not be resolved, else any of the following:
        - Keys(list): If the path is a key of a dictionary
        - Type: If the path is a value of a dictionary. Can be "Number", "String", "Array" or "Datetime

        Args:
            - type: The type of the data source
            - path: The path to resolve
            - data_source_url: The url of the data source

        Returns:
        The type of the path

        Example:

        >>> with TypesResolver() as tr:
        >>>     tr.resolve("AirQualityObserved", "address", "url")
        >>> ['addressCountry', 'addressLocality', 'addressRegion', 'district', 'postOfficeBoxNumber', 'postalCode', 'streetAddress', 'streetNr']
        >>>
        >>> with TypesResolver() as tr:
        >>>     tr.resolve("AirQualityObserved", "address.addressCountry", "url")
        >>> 'String'
        >>>
        >>> with TypesResolver() as tr:
        >>>     tr.resolve("AirQualityObserved", "Error", "url")
        >>> # None
        """

        if result := self._resolve_specs(type, path):
            return result

        if result := self._resolve_data(data_source_url, path):
            return result

        return None

    def _resolve_specs(self, type: str, path: str) -> List | Keys | Type | None:
        """"""

        specs = self._get_specs(type)
        to_return = None

        for p in path.split("."):
            if result := self._parse_standart(p):
                return result

            specs, to_return = self._resolve_type_from_specs(specs, p)

            if to_return is None:
                return None

        return to_return

    def _resolve_data(self, url: str, path: str) -> List | Keys | Type | None:
        """"""

        data = self._get_data(url)
        to_return = None

        for p in path.split("."):
            data, to_return = self._resolve_type_from_data(data, p)

            if to_return is None:
                return None

        return to_return

    def _get_specs(self, type: str) -> dict:
        """"""

        if not self._spec_cache.get(type):
            r = requests.get(self._urls[type])
            specs = load(r.text, Loader=Loader)
            self._spec_cache[type] = specs[type]["properties"]

        return self._spec_cache[type]

    def _get_data(self, url: str) -> dict:
        """"""

        if not self._data_cache.get(url):
            r = requests.get(url).json()[0]
            self._data_cache[url] = r

        return self._data_cache[url]

    def _resolve_type_from_specs(
        self, specs: dict, path: str
    ) -> tuple[dict, Type | None | Keys | List]:
        """"""

        specs = specs.get(path) or specs.get(path.lower().replace(".", ""))

        if not specs:
            return specs, None

        if specs["type"] == "object":
            to_return = Keys(specs["properties"].keys())
            specs = specs["properties"]
            return specs, to_return

        if specs["type"] == "array":
            if specs["items"]["type"] == "number":
                return specs, List.Number

            if specs["items"]["type"] == "string":
                return specs, List.String

            return specs, None

        if specs["type"] == "string":
            if specs.get("format") == "date-time":
                return specs, "Time"

            return specs, "String"

        if specs["type"] == "number":
            return specs, "Number"

        return specs, None

    def _resolve_type_from_data(
        self, data: dict, path: str
    ) -> tuple[dict, Type | Keys | List | None]:
        """"""

        value = data.get(path)

        if not value:
            return data, None

        type = value.get("type") if isinstance(value, dict) else None

        if type == "Number":
            return data, "Number"

        elif type == "Text":
            return data, "String"

        elif type == "DateTime":
            return data, "Time"

        elif type == "List":
            value = value["value"]

            if isinstance(value[0], int):
                return data, List.Number

            if isinstance(value[0], str):
                return data, List.String

            return data, None

        elif type == "URL":
            return data, "String"

        elif type == "geo:json":
            return data, List.Number

        elif type is None:
            if isinstance(value, dict):
                return value, Keys(value.keys())

            if isinstance(value, list):

                if isinstance(value[0], int):
                    return data, List.Number

                if isinstance(value[0], str):
                    return data, List.String

                return data, None

            if isinstance(value, str):
                return data, "String"

            if isinstance(value, int):
                return data, "Number"

            return data, None

        else:
            value = value["value"]

            if isinstance(value, dict):
                return value, Keys(value.keys())

            if isinstance(value, list):
                if isinstance(value[0], int):
                    return data, List.Number

                if isinstance(value[0], str):
                    return data, List.String

                return data, None

            return data, None

    def _parse_standart(self, path: str) -> List | None:
        if path.lower() == "location":
            return List.Number


if __name__ == "__main__":
    with TypesResolver() as tr:
        print(
            "stationName: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "stationName",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )
        print(
            "location: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "location",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )
        print(
            "address: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "address",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )
        print(
            "address.addressCountry: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "address.addressCountry",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )
        print(
            "NO2: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "NO2",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )
        print(
            "NOx: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "NOx",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )

        print(
            "validity: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "validity",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )

        print(
            "validity.to: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "validity.to",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )

        print(
            "dateObserved: {}".format(
                tr.resolve(
                    "AirQualityObserved",
                    "dateObserved",
                    data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
                )
            )
        )
