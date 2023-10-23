from typing import TypeAlias

from pydantic import BaseModel


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
    query: Query


class GeoMap(BaseModel):
    type: str
    source: str
    data: list[str]
    area: str | None  # center coordinates (https://nominatim.org/)


class PieChart(BaseModel):
    type: str
    source: str
    traces: list[str]
    pie_chart_type: str | None


class BarChart(BaseModel):
    type: str
    source: str
    traces: list[str]  # first trace is x axis


class TimeSeries(BaseModel):
    type: str
    source: str
    traces: list[str]  # first trace is x axis


class XYChart(BaseModel):
    type: str
    source: str
    traces: list[str]  # first trace is x axis


Panel: TypeAlias = PieChart | TimeSeries | BarChart | GeoMap | XYChart


class Application(BaseModel):
    type: str
    layout: str
    roles: list[str]
    panels: dict[str, Panel]


class Deployment(BaseModel):
    uri: str
    port: int
    type: str


class Config(BaseModel):
    service: Service
    data_sources: dict[str, Datasource]
    application: Application
    deployment: dict[str, dict[str, Deployment]]
