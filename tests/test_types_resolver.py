from types_resolver import TypesResolver

def test_some_cases():
    with TypesResolver() as tr:
        assert tr.resolve(
            "AirQualityObserved",
            "stationName",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) == "String"

        assert tr.resolve(
            "AirQualityObserved",
            "location",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) == "Array"

        result = tr.resolve(
            "AirQualityObserved",
            "address",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        )
        assert isinstance(result, list)
        assert result.sort() == ['addressCountry', 'addressLocality', 'addressRegion', 'district', 'postOfficeBoxNumber', 'postalCode', 'streetAddress', 'streetNr'].sort()

        assert tr.resolve(
            "AirQualityObserved",
            "address.addressCountry",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) == "String"

        assert tr.resolve(
            "AirQualityObserved",
            "NO2",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) == "Number"

        assert tr.resolve(
            "AirQualityObserved",
            "NOx",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) == "Number"

        result = tr.resolve(
            "AirQualityObserved",
            "validity",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        )
        assert isinstance(result, list)
        assert result.sort() == ['from', 'to'].sort()

        assert tr.resolve(
            "AirQualityObserved",
            "validity.to",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) == "String"

        assert tr.resolve(
            "AirQualityObserved",
            "dateObserved",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) == "String"

        assert tr.resolve(
            "AirQualityObserved",
            "Error",
            data_source_url="https://data.iiss.at/dataskop/fiwarenosec/v2/entities?type=AirQualityObserved",
        ) is None
