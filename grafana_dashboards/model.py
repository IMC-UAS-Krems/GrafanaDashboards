from typing import Annotated, Literal, TypeAlias

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


class Datasource(BaseModel):
    provider: str  # Fiware
    type: str  # ignore
    uri: str
    query: str


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


Panel: TypeAlias = PieChart | TimeSeries | BarChart | GeoMap | XYChart


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
