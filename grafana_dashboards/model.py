from enum import Enum
from typing import Annotated, Literal, TypeAlias
import base64
import secrets

from pydantic import BaseModel, Field


class Version(BaseModel):
    major: int
    minor: int
    patch: int


class Service(BaseModel):
    title: str
    scope: str  # Fiware scope
    version: Version


class Query(BaseModel):
    type: str


class DataSourceConfig(BaseModel):
    company: int
    measurements: dict[str, int]
    token: str


class DataSourceProvider(str, Enum):
    Dataskop = "Dataskop"
    Fiware = "Fiware"


class Datasource(BaseModel):
    provider: DataSourceProvider
    type: str  # ignore
    uri: str
    query: str | None = None
    config: DataSourceConfig
    uid: str | None = None

    def model_post_init(self, __context):
        self.uid = self.generate_uid()

    def generate_uid(self):
        # return (
        #     base64.urlsafe_b64encode(secrets.token_bytes(9)).decode("utf-8").rstrip("=")
        # )
        if self.provider == DataSourceProvider.Dataskop:
            return "vS7bVH14k"
        else:
            return "b66da1e5-11fc-4567-a063-e2169c55c71d"


class GeoMap(BaseModel):
    type: Literal["geomap"]
    source: str
    data: list[str]
    area: str | None = Field(None)  # center coordinates (https://nominatim.org/)


class PieChart(BaseModel):
    type: Literal["pie_chart"]
    source: str
    traces: list[str]
    pie_chart_type: str | None = Field(None)


class BarChart(BaseModel):
    type: Literal["bar_chart"]
    source: str
    traces: list[str]  # first trace is x axis


class TimeSeries(BaseModel):
    type: Literal["timeseries"]
    source: str
    traces: list[str]  # first trace is x axis


class XYChart(BaseModel):
    type: Literal["xy_chart"]
    source: str
    traces: list[str]  # first trace is x axis


class SingleLine(BaseModel):
    type: Literal["smartcomm-simpleline-panel"]
    source: str
    traces: list[str]


class Calendar(BaseModel):
    type: Literal["smartcomm-calendar-panel"]
    source: str
    locations: list[str]
    traces: list[str]


class MultiLine(BaseModel):
    type: Literal["smartcomm-multiplelinechart-panel"]
    source: str
    locations: list[str]
    traces: list[str]


class ExtremeValues(BaseModel):
    type: Literal["smartcomm-extremevalues-panel"]
    source: str
    locations: list[str]
    traces: list[str]


class BulletGraph(BaseModel):
    type: Literal["smartcomm-bulletgraph-panel"]
    source: str
    locations: list[str]
    traces: list[str]

class BarsBubbles(BaseModel):
    type: Literal["smartcomm-minmaxbarchart-panel"]
    source: str
    locations: list[str]
    traces: list[str]


class MapFHSTP(BaseModel):
    type: Literal["smartcomm-map-panel"]
    source: str
    traces: list[str]


Panel: TypeAlias = (
    PieChart
    | TimeSeries
    | BarChart
    | GeoMap
    | XYChart
    | SingleLine
    | Calendar
    | MultiLine
    | ExtremeValues
    | BulletGraph
    | MapFHSTP
    | BarsBubbles
)


class Application(BaseModel):
    type: str
    layout: str
    roles: list[str]
    panels: dict[str, Annotated[Panel, Field(discriminator="type")]]


class Deployment(BaseModel):
    uri: str
    port: int
    type: str


class Data(BaseModel):
    sources: dict[str, Datasource]


class Config(BaseModel):
    service: Service
    data: Data
    application: Application
    deployment: dict[str, dict[str, Deployment]]
