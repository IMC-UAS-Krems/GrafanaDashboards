from grafana_dashboards.types_resolver import List, TypesResolver
from pytest import fixture
import requests


@fixture
def types_resolver():
    return TypesResolver()


@fixture
def air_quality_observed_schema(types_resolver: TypesResolver):
    model = types_resolver._get_schema("AirQualityObserved")
    return model


@fixture
def air_quality_observed_data(types_resolver: TypesResolver):
    data = types_resolver._get_data(
        "https://data.iiss.at/dataskop/fiwarenosec/v2/entities", "AirQualityObserved"
    )
    return data


def test_some_cases():
    tr = TypesResolver()
    assert (
        tr.resolve(
            "AirQualityObserved",
            "stationName",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        == "string"
    )

    assert (
        tr.resolve(
            "AirQualityObserved",
            "location",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        == List.Number
    )

    result = tr.resolve(
        "AirQualityObserved",
        "address",
        data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
    )
    assert isinstance(result, list)
    assert (
        result.sort()
        == [
            "addressCountry",
            "addressLocality",
            "addressRegion",
            "district",
            "postOfficeBoxNumber",
            "postalCode",
            "streetAddress",
            "streetNr",
        ].sort()
    )

    assert (
        tr.resolve(
            "AirQualityObserved",
            "address.addressCountry",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        == "string"
    )

    assert (
        tr.resolve(
            "AirQualityObserved",
            "NO2",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        == "number"
    )

    assert (
        tr.resolve(
            "AirQualityObserved",
            "NOx",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        == "number"
    )

    result = tr.resolve(
        "AirQualityObserved",
        "validity",
        data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
    )
    assert isinstance(result, list)
    assert result.sort() == ["from", "to"].sort()

    assert (
        tr.resolve(
            "AirQualityObserved",
            "validity.to",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        == "string"
    )

    assert (
        tr.resolve(
            "AirQualityObserved",
            "dateObserved",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        == "time"
    )

    assert (
        tr.resolve(
            "AirQualityObserved",
            "Error",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities",
        )
        is None
    )


def test_air_quality_observe(
    types_resolver: TypesResolver, air_quality_observed_schema
):
    present_fileds = [
        "address",
        "airQualityIndex",
        "airQualityLevel",
        "alternateName",
        "areaServed",
        "as",
        "c6h6",
        "cd",
        "co",
        "co2",
        "coLevel",
        "dataProvider",
        "dateCreated",
        "dateModified",
        "dateObserved",
        "description",
        "id",
        "location",
        "name",
        "ni",
        "no",
        "no2",
        "nox",
        "o3",
        "owner",
        "pb",
        "pm1",
        "pm10",
        "pm25",
        "precipitation",
        "refDevice",
        "refPointOfInterest",
        "refWeatherObserved",
        "relativeHumidity",
        "reliability",
        "seeAlso",
        "sh2",
        "so2",
        "source",
        "temperature",
        "type",
        "typeofLocation",
        "volatileOrganicCompoundsTotal",
        "windDirection",
        "windSpeed",
    ]

    for field in present_fileds:
        assert (
            types_resolver._resolve_type_from_specs(air_quality_observed_schema, field)[
                1
            ]
            is not None
        )

    assert (
        types_resolver._resolve_type_from_specs(
            air_quality_observed_schema, "stationName"
        )[1]
        is None
    )

    assert (
        types_resolver._resolve_type_from_specs(
            air_quality_observed_schema, "stationCode"
        )[1]
        is None
    )


def test_air_quality_observed_data(
    types_resolver: TypesResolver, air_quality_observed_data: dict
):
    for field in air_quality_observed_data:
        assert (
            types_resolver._resolve_type_from_data(air_quality_observed_data, field)
            is not None
        )


def test_air_quality_observed(types_resolver: TypesResolver):
    data = requests.get(
        "https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved&limit=1000"
    ).json()

    for entity in data:
        for field in entity:
            assert types_resolver._resolve_type_from_data(entity, field) is not None
