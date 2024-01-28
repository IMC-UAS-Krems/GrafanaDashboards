from typing import Literal, TypeAlias
from enum import Enum
import logging

import jsonref
import requests

Type: TypeAlias = Literal["number", "string", "time", "boolean"]
GrafanaSpecDict: TypeAlias = dict[str, dict]


class Keys(list):
    pass


class List(Enum):
    Number = "number"
    String = "string"
    Time = "time"
    Boolean = "boolean"


class TypesResolver:
    """
    This class is used to resolve the type of a given path in a given type or data source

    >>> type_resolver = TypesResolver()
    >>> type_resolver.resolve("fiware_model_type", "path", "url")
    """

    def __init__(self) -> None:
        self._schema_cache: list[tuple[str, dict]] = []  # TODO: LinkedList? Maybe...
        self._data_cache: tuple[str, dict] = ("", {})
        self._SCHEMA_CHACHE_MAX_LEN = 5
        self._schema_deref = SchemaDeref()
        self._logger = logging.getLogger("grafana_dashboards.types_resolver")
        # TODO: load from file or resolve from github
        self._urls = {
            "AirQualityObserved": "https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/AirQualityObserved/schema.json",
            "PointOfInterest": "https://raw.githubusercontent.com/smart-data-models/dataModel.PointOfInterest/master/PointOfInterest/schema.json",
        }
        self._logger.setLevel(logging.INFO)

    def resolve(
        self, model_type: str, path_to_resolve: str, data_source_url: str
    ) -> List | Keys | Type | None:
        """
        Tries to resolve the type of a given path in a given type or data source. First, it tries to resolve a type from the model, if it fails,
        it tries to resolve it from the first item in the data source

        Returns `None` if the path could not be resolved, else any of the following:
        - Keys(list): If the path is a key of a dictionary
        - Type: If the path is a value of a dictionary. Can be "number", "string", "array" or "time"

        Args:
            - model_type: The type of the data source
            - path_to_resolve: The path to resolve
            - data_source_url: The url of the data source

        Returns:
        The type of the path

        Example:
        ```python
        tr = TypesResolver()
        tr.resolve("AirQualityObserved", "address", "url")
        # ['addressCountry', 'addressLocality', 'addressRegion', 'district', 'postOfficeBoxNumber', 'postalCode', 'streetAddress', 'streetNr']

        tr = TypesResolver()
        tr.resolve("AirQualityObserved", "address.addressCountry", "url")
        # 'string'

        tr = TypesResolver()
        tr.resolve("AirQualityObserved", "Error", "url")
        # None
        ```
        """

        if result := self._parse_standart(path_to_resolve):
            return result

        if result := self._resolve_schema(model_type, path_to_resolve):
            return result

        self._logger.debug(
            f"Could not resolve {model_type}: {path_to_resolve} from schema"
        )

        if result := self._resolve_data(data_source_url, path_to_resolve, model_type):
            return result

        return None

    def _resolve_schema(
        self, url: str, path_to_resolve: str
    ) -> List | Keys | Type | None:
        """"""
        schema = self._get_schema(url)
        to_return = None

        for p in path_to_resolve.split("."):
            schema, to_return = self._resolve_type_from_specs(schema, p)

            if to_return is None:
                return None

        return to_return

    def _resolve_data(
        self, url: str, path_to_resolve: str, model_type: str
    ) -> List | Keys | Type | None:
        """"""

        data = self._get_data(url, model_type)
        to_return = None

        for p in path_to_resolve.split("."):
            data, to_return = self._resolve_type_from_data(data, p)

            if to_return is None:
                return None

        return to_return

    def _get_schema(self, model_type: str) -> dict:
        """"""
        for i, (t, schema) in enumerate(self._schema_cache):
            if t == model_type:
                self._logger.debug(f"Schema cache hit for {model_type}")
                self._schema_cache.pop(i)
                self._schema_cache.insert(0, (t, schema))

                return schema

        self._logger.debug(f"Schema cache miss for {model_type}")

        r = requests.get(self._urls[model_type])
        schema = self._schema_deref.expand(r.text)["properties"]

        self._schema_cache.insert(0, (model_type, schema))

        if len(self._schema_cache) > self._SCHEMA_CHACHE_MAX_LEN:
            self._schema_cache.pop()

        return schema

    def _get_data(self, url: str, model_type: str) -> dict:
        """"""

        if self._data_cache[0] != type:
            r = requests.get(url, params={"type": model_type, "limit": 1}).json()[0]
            self._data_cache = (model_type, r)

        return self._data_cache[1]

    def _resolve_type_from_specs(
        self, spec: GrafanaSpecDict, path_to_resolve: str
    ) -> tuple[dict, Type | None | Keys | List]:
        """"""

        field = spec.get(path_to_resolve) or spec.get(
            path_to_resolve.lower().replace(".", "")
        )

        if not field:
            return {}, None

        if field.get("anyOf"):
            field = field["anyOf"][0]

        if field.get("oneOf"):
            field = field["oneOf"][0]

        if field["type"] == "object":
            to_return = Keys(field["properties"].keys())
            field = field["properties"]
            return field, to_return

        if field["type"] == "array":
            if field["items"].get("anyOf"):
                field["items"] = field["items"]["anyOf"][0]

            if field["items"].get("oneOf"):
                field["items"] = field["items"]["oneOf"][0]

            if field["items"]["type"] == "number":
                return field, List.Number

            if field["items"]["type"] == "string":
                return field, List.String

            return field, None

        if field["type"] == "string":
            if field.get("format") == "date-time":
                return field, "time"

            return field, "string"

        if field["type"] == "number":
            return field, "number"

        return field, None

    def _resolve_type_from_data(
        self, data: dict, path_to_resolve: str
    ) -> tuple[dict, Type | Keys | List | None]:
        """"""

        value = data.get(path_to_resolve)

        if not value:
            return data, None

        type = value.get("type") if isinstance(value, dict) else None

        if type == "Number":
            return data, "number"

        elif type == "Text":
            return data, "string"

        elif type == "DateTime":
            return data, "time"

        elif type == "List":
            value = value["value"]

            if isinstance(value[0], int):
                return data, List.Number

            if isinstance(value[0], str):
                return data, List.String

            return data, None

        elif type == "URL":
            return data, "string"

        elif type == "geo:json":
            return data, List.Number

        elif type is None:  # is not a dict
            if isinstance(value, dict):
                return value, Keys(value.keys())

            if isinstance(value, list):
                if isinstance(value[0], int):
                    return data, List.Number

                if isinstance(value[0], str):
                    return data, List.String

                return data, None

            if isinstance(value, str):
                return data, "string"

            if isinstance(value, int):
                return data, "number"

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

    def _parse_standart(self, path_to_resolve: str) -> Type | List | None:
        if path_to_resolve.lower() == "location":
            return List.Number

        return None


class SchemaDeref:
    """
    Code is from Fiware

    See: https://github.com/smart-data-models/data-models/blob/master/utils/10_model.yaml_v13.py
    """

    def __init__(self) -> None:
        self.propertyTypes = ["Property", "Relationship", "GeoProperty"]

    def open_jsonref(self, json_schema: str) -> dict:
        return jsonref.loads(json_schema)  # type: ignore

    def parse_description(self, schemaPayload):
        output = {}
        purgedDescription = str(schemaPayload["description"]).replace(chr(34), "")
        separatedDescription = purgedDescription.split(". ")
        copiedDescription = list.copy(separatedDescription)

        for descriptionPiece in separatedDescription:
            if descriptionPiece in self.propertyTypes:
                output["type"] = descriptionPiece
                copiedDescription.remove(descriptionPiece)
            elif descriptionPiece.find("Model:") > -1:
                copiedDescription.remove(descriptionPiece)
                output["model"] = descriptionPiece.replace("'", "").replace(
                    "Model:", ""
                )

            if descriptionPiece.find("Units:") > -1:
                copiedDescription.remove(descriptionPiece)
                output["units"] = descriptionPiece.replace("'", "").replace(
                    "Units:", ""
                )
        description = ". ".join(copiedDescription)

        return output, description

    def parse_payload(self, schemaPayload, level):
        output = {}
        if level == 1:
            if "allOf" in schemaPayload:
                for index in range(len(schemaPayload["allOf"])):
                    if "definitions" in schemaPayload["allOf"][index]:
                        partialOutput = self.parse_payload(
                            schemaPayload["allOf"][index]["definitions"], level + 1
                        )
                        output = dict(output, **partialOutput)
                    elif "properties" in schemaPayload["allOf"][index]:
                        partialOutput = self.parse_payload(
                            schemaPayload["allOf"][index], level + 1
                        )
                        output = dict(output, **partialOutput["properties"])
                    else:
                        partialOutput = self.parse_payload(
                            schemaPayload["allOf"][index], level + 1
                        )
                        output = dict(output, **partialOutput)
            if "anyOf" in schemaPayload:
                for index in range(len(schemaPayload["anyOf"])):
                    if "definitions" in schemaPayload["anyOf"][index]:
                        partialOutput = self.parse_payload(
                            schemaPayload["anyOf"][index]["definitions"], level + 1
                        )
                        output = dict(output, **partialOutput)
                    elif "properties" in schemaPayload["anyOf"][index]:
                        partialOutput = self.parse_payload(
                            schemaPayload["anyOf"][index], level + 1
                        )
                        output = dict(output, **partialOutput["properties"])
                    else:
                        partialOutput = self.parse_payload(
                            schemaPayload["anyOf"][index], level + 1
                        )
                        output = dict(output, **partialOutput)
            if "oneOf" in schemaPayload:
                for index in range(len(schemaPayload["oneOf"])):
                    if "definitions" in schemaPayload["oneOf"][index]:
                        partialOutput = self.parse_payload(
                            schemaPayload["oneOf"][index]["definitions"], level + 1
                        )
                        output = dict(output, **partialOutput)
                    elif "properties" in schemaPayload["oneOf"][index]:
                        partialOutput = self.parse_payload(
                            schemaPayload["oneOf"][index], level + 1
                        )
                        output = dict(output, **partialOutput["properties"])
                    else:
                        partialOutput = self.parse_payload(
                            schemaPayload["oneOf"][index], level + 1
                        )
                        output = dict(output, **partialOutput)

            if "properties" in schemaPayload:
                output = self.parse_payload(schemaPayload["properties"], level + 1)

        elif level < 8:
            if isinstance(schemaPayload, dict):
                for subschema in schemaPayload:
                    if subschema in ["allOf", "anyOf", "oneOf"]:
                        output[subschema] = []
                        for index in range(len(schemaPayload[subschema])):
                            if "properties" in schemaPayload[subschema][index]:
                                partialOutput = self.parse_payload(
                                    schemaPayload[subschema][index], level + 1
                                )
                                output[subschema].append(partialOutput["properties"])
                            else:
                                partialOutput = self.parse_payload(
                                    schemaPayload[subschema][index], level + 1
                                )
                                output[subschema].append(partialOutput)

                    elif subschema == "properties":
                        output[subschema] = {}
                        for prop in schemaPayload["properties"]:
                            try:
                                output[subschema][prop]
                            except Exception:
                                output[subschema][prop] = {}
                            for item in list(schemaPayload["properties"][prop]):
                                if item in ["allOf", "anyOf", "oneOf"]:
                                    output[subschema][prop][item] = []
                                    for index in range(
                                        len(schemaPayload[subschema][prop][item])
                                    ):
                                        output[subschema][prop][item].append(
                                            self.parse_payload(
                                                schemaPayload[subschema][prop][item][
                                                    index
                                                ],
                                                level + 1,
                                            )
                                        )
                                elif item == "description":
                                    _, description = self.parse_description(
                                        schemaPayload[subschema][prop]
                                    )
                                    output[subschema][prop][item] = description

                                elif item == "items":
                                    output[subschema][prop][item] = self.parse_payload(
                                        schemaPayload[subschema][prop][item], level + 1
                                    )
                                elif item == "properties":
                                    output[subschema][prop][item] = self.parse_payload(
                                        schemaPayload[subschema][prop][item], level + 1
                                    )
                                elif item == "type":
                                    if (
                                        schemaPayload[subschema][prop][item]
                                        == "integer"
                                    ):
                                        output[subschema][prop][item] = "number"
                                    else:
                                        output[subschema][prop][item] = schemaPayload[
                                            subschema
                                        ][prop][item]
                                else:
                                    output[subschema][prop][item] = schemaPayload[
                                        subschema
                                    ][prop][item]

                    elif isinstance(schemaPayload[subschema], dict):
                        output[subschema] = self.parse_payload(
                            schemaPayload[subschema], level + 1
                        )
                    else:
                        if subschema == "description":
                            _, description = self.parse_description(schemaPayload)
                            output[subschema] = description
                        else:
                            output[subschema] = schemaPayload[subschema]

            elif isinstance(schemaPayload, list):
                for index in range(len(schemaPayload)):
                    partialOutput = self.parse_payload(schemaPayload[index], level + 1)
                    output = dict(output, **partialOutput)
        else:
            return None

        return output

    def expand(self, json_schema: str) -> dict:
        result = {}
        schemaExpanded = self.open_jsonref(json_schema)
        result["properties"] = self.parse_payload(schemaExpanded, 1)
        try:  # the required clause is optional
            required = schemaExpanded["required"]
        except Exception:
            required = []

        result["type"] = "object"
        result["required"] = required

        return result


# if __name__ == "__main__":
#     with TypesResolver() as tr:
#         print(
#             "stationName: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "stationName",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#         print(
#             "location: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "location",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#         print(
#             "address: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "address",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#         print(
#             "address.addressCountry: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "address.addressCountry",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#         print(
#             "NO2: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "NO2",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#         print(
#             "NOx: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "NOx",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#
#         print(
#             "validity: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "validity",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#
#         print(
#             "validity.to: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "validity.to",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
#
#         print(
#             "dateObserved: {}".format(
#                 tr.resolve(
#                     "AirQualityObserved",
#                     "dateObserved",
#                     data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
#                 )
#             )
#         )
