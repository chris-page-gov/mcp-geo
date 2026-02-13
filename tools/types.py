from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class DPAEntry(TypedDict, total=False):
    UPRN: NotRequired[str]
    ADDRESS: NotRequired[str]
    LAT: NotRequired[str | float | int]
    LNG: NotRequired[str | float | int]
    CLASS: NotRequired[str]
    CLASSIFICATION_CODE: NotRequired[str]
    CLASSIFICATION_CODE_DESCRIPTION: NotRequired[str]
    LOCAL_CUSTODIAN_CODE: NotRequired[str | float | int]

class DPAResult(TypedDict, total=False):
    DPA: DPAEntry

class GazetteerEntry(TypedDict, total=False):
    ID: NotRequired[str]
    NAME1: NotRequired[str]
    TYPE: NotRequired[str]
    LOCAL_TYPE: NotRequired[str]
    GEOMETRY: NotRequired[Any]
    DISTANCE: NotRequired[float | int | str]

class GazetteerResult(TypedDict, total=False):
    GAZETTEER_ENTRY: GazetteerEntry

class PlacesResponse(TypedDict, total=False):
    results: list[DPAResult]

class NamesResponse(TypedDict, total=False):
    results: list[GazetteerResult]

JsonDict = dict[str, Any]
