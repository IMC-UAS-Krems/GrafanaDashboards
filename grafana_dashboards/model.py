from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel


class Config(BaseModel):
    service: Service
    data_sources: dict[str, Datasource]
    application: Application
    deployment: dict[str, dict[str, Deployment]]


class Version(BaseModel):
    major: int
    minor: int
    patch: int


class Service(BaseModel):
    title: str
    scope: str
    version: Version


class Query(BaseModel):
    type: str


class Datasource(BaseModel):
    provider: str
    type: str
    uri: str
    query: Query


class GeoMap(BaseModel):
    type: str
    source: str
    data: list[str]
    area: str | None


class PieChart(BaseModel):
    type: str
    source: str
    traces: list[str]
    pie_chart_type: str | None


class BarChart(BaseModel):
    type: str
    source: str
    traces: list[str]


class TimeSeries(BaseModel):
    type: str
    source: str
    traces: list[str]


class XYChart(BaseModel):
    type: str
    source: str
    traces: list[str]


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
