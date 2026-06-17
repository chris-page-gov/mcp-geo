from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GeographyLevel:
    key: str
    label: str
    rank: int
    area_level: str | None = None
    normalized_key: str | None = None
    semantic_key: str | None = None
    column: str | None = None
    admin_level: str | None = None
    selector: bool = False
    map_focus_level: str | None = None
    area_summary: bool = False
    area_summary_rank: int | None = None
    nomis_preferred: bool = False
    stats_comparison: bool = False
    admin_search_priority: int | None = None
    aliases: tuple[str, ...] = ()
    keyword_patterns: tuple[str, ...] = ()
    code_patterns: tuple[str, ...] = ()
    nomis_type_matchers: tuple[str, ...] = ()
    display_name_policy: str | None = None

    def selector_option(self) -> dict[str, Any]:
        option: dict[str, Any] = {
            "value": self.key,
            "label": self.label,
            "mapFocusLevel": self.map_focus_level,
        }
        if self.area_level:
            option["areaLevel"] = self.area_level
        if self.display_name_policy:
            option["displayNamePolicy"] = self.display_name_policy
        return option


GEOGRAPHY_LEVELS: tuple[GeographyLevel, ...] = (
    GeographyLevel(
        key="oa",
        label="OA",
        rank=0,
        area_level="OA",
        normalized_key="oa",
        semantic_key="oa_code",
        column="oa_code",
        admin_level="OA",
        selector=True,
        map_focus_level="OA",
        area_summary=True,
        area_summary_rank=0,
        nomis_preferred=True,
        admin_search_priority=8,
        aliases=("OUTPUT_AREA",),
        keyword_patterns=(r"\boa\b", r"\boutput areas?\b"),
        code_patterns=(r"[EW]00\d{6}",),
        nomis_type_matchers=("output area",),
    ),
    GeographyLevel(
        key="lsoa",
        label="LSOA",
        rank=1,
        area_level="LSOA",
        normalized_key="lsoa",
        semantic_key="lsoa_code",
        column="lsoa_code",
        admin_level="LSOA",
        selector=True,
        map_focus_level="LSOA",
        area_summary=True,
        area_summary_rank=1,
        nomis_preferred=True,
        stats_comparison=True,
        admin_search_priority=7,
        aliases=(),
        keyword_patterns=(r"\blsoa\b", r"\blower (layer )?super output areas?\b"),
        code_patterns=(r"[EW]01\d{6}",),
        nomis_type_matchers=("lower layer", "lsoa"),
    ),
    GeographyLevel(
        key="msoa",
        label="MSOA",
        rank=2,
        area_level="MSOA",
        normalized_key="msoa",
        semantic_key="msoa_code",
        column="msoa_code",
        admin_level="MSOA",
        selector=True,
        map_focus_level="MSOA",
        area_summary=True,
        area_summary_rank=2,
        nomis_preferred=True,
        stats_comparison=True,
        admin_search_priority=6,
        aliases=(),
        keyword_patterns=(r"\bmsoa\b", r"\bmiddle (layer )?super output areas?\b"),
        code_patterns=(r"[EW]02\d{6}",),
        nomis_type_matchers=("middle layer", "msoa"),
        display_name_policy="preserve official currentName; expose HoC displayName separately",
    ),
    GeographyLevel(
        key="parish",
        label="Parish / PARNCP",
        rank=3,
        area_level="PARISH",
        normalized_key="parish",
        semantic_key="parish_code",
        column="parish_code",
        admin_level="PARISH",
        selector=True,
        map_focus_level="PARISH",
        area_summary=True,
        area_summary_rank=None,
        stats_comparison=True,
        admin_search_priority=1,
        aliases=(
            "PARISHES",
            "PARNCP",
            "PARNCP_AREA",
            "PARNCP_AREAS",
            "CIVIL_PARISH",
            "CIVIL_PARISHED",
            "NON_CIVIL_PARISHED",
            "NON_CIVIL_PARISHED_AREA",
        ),
        keyword_patterns=(
            r"\bparish(es)?\b",
            r"\bparncp\b",
            r"\bnon[- ]civil[- ]parished\b",
        ),
        code_patterns=(r"([EW]04|E43)\d{6}",),
        nomis_type_matchers=(
            "parish",
            "parishes",
            "civil parish",
            "community",
            "communities",
            "non-civil",
            "non civil",
            "parncp",
        ),
    ),
    GeographyLevel(
        key="ward",
        label="Ward",
        rank=4,
        area_level="WARD",
        normalized_key="ward",
        semantic_key="ward_code",
        column="ward_code",
        admin_level="WARD",
        selector=True,
        map_focus_level="WARD",
        area_summary=True,
        area_summary_rank=4,
        stats_comparison=True,
        admin_search_priority=0,
        aliases=("WD",),
        keyword_patterns=(r"\bwards?\b",),
        code_patterns=(r"[EW]05\d{6}",),
        nomis_type_matchers=("ward",),
    ),
    GeographyLevel(
        key="parl_const",
        label="Parliamentary Constituency",
        rank=5,
        selector=True,
        aliases=("PARLIAMENTARY_CONSTITUENCY",),
        keyword_patterns=(r"\bconstituenc(y|ies)\b", r"\bparliamentary\b", r"\bmp\b"),
    ),
    GeographyLevel(
        key="local_auth",
        label="Local Authority",
        rank=6,
        area_level="DISTRICT",
        normalized_key="lad",
        semantic_key="lad_code",
        column="lad_code",
        admin_level="DISTRICT",
        selector=True,
        map_focus_level="DISTRICT",
        area_summary=True,
        area_summary_rank=5,
        admin_search_priority=2,
        aliases=("LAD", "LA", "LOCAL_AUTHORITY", "LOCAL_AUTHORITY_DISTRICT"),
        keyword_patterns=(
            r"\blocal authority\b",
            r"\bcouncil\b",
            r"\bdistricts?\b",
            r"\bboroughs?\b",
            r"\blad\b",
        ),
        code_patterns=(r"(E06|E07|E08|E09|W06)\d{6}",),
        nomis_type_matchers=("local authorit", "district"),
    ),
    GeographyLevel(
        key="county",
        label="County / Unitary Authority",
        rank=7,
        admin_level="COUNTY",
        map_focus_level="COUNTY",
        admin_search_priority=3,
        aliases=("COUNTY_UNITARY", "COUNTY_UNITARY_AUTHORITY", "CTYUA"),
        keyword_patterns=(r"\bcount(y|ies)\b",),
    ),
    GeographyLevel(
        key="region",
        label="Region",
        rank=8,
        area_level="REGION",
        normalized_key="region",
        semantic_key="region_code",
        column="region_code",
        admin_level="REGION",
        selector=True,
        map_focus_level="REGION",
        area_summary=True,
        area_summary_rank=6,
        admin_search_priority=4,
        aliases=("RGN",),
        keyword_patterns=(r"\bregions?\b",),
        code_patterns=(r"[EW]12\d{6}",),
    ),
    GeographyLevel(
        key="country",
        label="Country / Nation",
        rank=9,
        area_level="COUNTRY",
        normalized_key="country",
        semantic_key="country_code",
        column="country_code",
        admin_level="NATION",
        selector=True,
        map_focus_level="NATION",
        area_summary=True,
        area_summary_rank=7,
        admin_search_priority=5,
        aliases=("CTRY", "NATION", "NATIONAL", "UK"),
        keyword_patterns=(
            r"\bcountr(y|ies)\b",
            r"\bnation\b",
            r"\bnational\b",
            r"\bnationwide\b",
        ),
        code_patterns=(r"[EWNS]92\d{6}",),
    ),
    GeographyLevel(
        key="built_up_area",
        label="Built-up Area",
        rank=10,
        selector=True,
        aliases=("BUA", "BUILT_UP_AREA"),
        keyword_patterns=(r"\bbuilt[- ]?up area\b", r"\bbua\b"),
    ),
    GeographyLevel(
        key="postcode",
        label="Postcode",
        rank=11,
        selector=True,
        keyword_patterns=(r"\bpostcode\b",),
    ),
)

LEVEL_BY_KEY: dict[str, GeographyLevel] = {level.key: level for level in GEOGRAPHY_LEVELS}
LEVEL_BY_AREA_LEVEL: dict[str, GeographyLevel] = {
    level.area_level: level for level in GEOGRAPHY_LEVELS if level.area_level
}
LEVEL_KEYWORDS: dict[str, list[str]] = {
    level.key: list(level.keyword_patterns)
    for level in GEOGRAPHY_LEVELS
    if level.keyword_patterns
}
LEVEL_RANK: dict[str, int] = {level.key: level.rank for level in GEOGRAPHY_LEVELS}
ADMIN_LEVEL_MAP: dict[str, str | None] = {
    level.key: level.admin_level for level in GEOGRAPHY_LEVELS
}
AREA_LEVEL_COLUMN_MAP: dict[str, str] = {
    level.area_level: level.column
    for level in GEOGRAPHY_LEVELS
    if level.area_level and level.column
}
AREA_SUMMARY_LEVELS: dict[str, dict[str, str]] = {
    level.area_level: {
        "normalizedKey": level.normalized_key or "",
        "semanticKey": level.semantic_key or "",
    }
    for level in GEOGRAPHY_LEVELS
    if level.area_summary and level.area_level and level.normalized_key and level.semantic_key
}
AREA_SUMMARY_LEVEL_RANK: dict[str, int] = {
    level.area_level: level.area_summary_rank
    for level in GEOGRAPHY_LEVELS
    if level.area_summary and level.area_level and level.area_summary_rank is not None
}
NOMIS_LOCAL_LEVEL_KEYS: frozenset[str] = frozenset(
    level.key for level in GEOGRAPHY_LEVELS if level.nomis_preferred
)
STATS_COMPARISON_LEVELS: tuple[str, ...] = tuple(
    level.area_level
    for level in GEOGRAPHY_LEVELS
    if level.stats_comparison and level.area_level
)
NOMIS_GEOGRAPHY_TYPE_MATCHERS: dict[str, tuple[str, ...]] = {
    level.area_level: level.nomis_type_matchers
    for level in GEOGRAPHY_LEVELS
    if level.area_level and level.nomis_type_matchers
}
ONS_SELECT_GEOGRAPHY_LEVELS: dict[str, str] = {
    "OA": "oa",
    "LSOA": "lsoa",
    "MSOA": "msoa",
    "PARISH": "parish",
    "WARD": "ward",
    "DISTRICT": "local_authority",
    "REGION": "region",
    "COUNTRY": "nation",
}


def _alias_key(value: str) -> str:
    return value.strip().upper().replace(" ", "_").replace("-", "_")


AREA_LEVEL_ALIASES: dict[str, str] = {}
for _level in GEOGRAPHY_LEVELS:
    if _level.area_level:
        AREA_LEVEL_ALIASES[_alias_key(_level.area_level)] = _level.area_level
        AREA_LEVEL_ALIASES[_alias_key(_level.key)] = _level.area_level
    for _alias in _level.aliases:
        if _level.area_level:
            AREA_LEVEL_ALIASES[_alias_key(_alias)] = _level.area_level

ADMIN_LEVEL_ALIASES: dict[str, str] = {}
for _level in GEOGRAPHY_LEVELS:
    if not _level.admin_level:
        continue
    ADMIN_LEVEL_ALIASES[_alias_key(_level.admin_level)] = _level.admin_level
    ADMIN_LEVEL_ALIASES[_alias_key(_level.key)] = _level.admin_level
    for _alias in _level.aliases:
        ADMIN_LEVEL_ALIASES[_alias_key(_alias)] = _level.admin_level

_AREA_LEVEL_CODE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern), level.area_level)
    for level in GEOGRAPHY_LEVELS
    if level.area_level
    for pattern in level.code_patterns
)


def selector_level_options() -> list[dict[str, Any]]:
    return [level.selector_option() for level in GEOGRAPHY_LEVELS if level.selector]


def selector_level_values() -> tuple[str, ...]:
    return tuple(level.key for level in GEOGRAPHY_LEVELS if level.selector)


def map_focus_level_for_selector(value: str) -> str | None:
    level = LEVEL_BY_KEY.get(value.strip().lower())
    return level.map_focus_level if level else None


def normalize_area_level(value: str) -> str | None:
    return AREA_LEVEL_ALIASES.get(_alias_key(value))


def normalize_admin_level(value: Any) -> str | None:
    if value is None:
        return None
    return ADMIN_LEVEL_ALIASES.get(_alias_key(str(value)))


def infer_admin_levels_from_text(text: str) -> list[str] | None:
    lowered = text.lower()
    for level in sorted(GEOGRAPHY_LEVELS, key=lambda item: item.rank):
        if not level.admin_level:
            continue
        if any(re.search(pattern, lowered) for pattern in level.keyword_patterns):
            return [level.admin_level]
    return None


def boundary_search_priority_levels() -> tuple[str, ...]:
    levels = [
        level
        for level in GEOGRAPHY_LEVELS
        if level.admin_level and level.admin_search_priority is not None
    ]
    ordered = sorted(levels, key=lambda item: item.admin_search_priority or 0)
    return tuple(level.admin_level for level in ordered if level.admin_level)


def infer_area_level_from_code(value: str) -> str | None:
    code = value.strip().upper()
    for pattern, area_level in _AREA_LEVEL_CODE_PATTERNS:
        if pattern.fullmatch(code):
            return area_level
    return None


def area_summary_target_is_compatible(anchor_level: str, target_level: str) -> bool:
    anchor = normalize_area_level(anchor_level)
    target = normalize_area_level(target_level)
    if anchor is None or target is None:
        return False
    if anchor == target:
        return True
    anchor_rank = AREA_SUMMARY_LEVEL_RANK.get(anchor)
    target_rank = AREA_SUMMARY_LEVEL_RANK.get(target)
    if not isinstance(anchor_rank, int) or not isinstance(target_rank, int):
        return False
    return target_rank >= anchor_rank


def normalize_ons_select_geography_level(value: str) -> str | None:
    raw = value.strip().lower()
    if not raw:
        return None
    area_level = normalize_area_level(value)
    if area_level and area_level in ONS_SELECT_GEOGRAPHY_LEVELS:
        return ONS_SELECT_GEOGRAPHY_LEVELS[area_level]
    admin_level = normalize_admin_level(value)
    if admin_level == "NATION":
        return "nation"
    return raw


def ons_select_geography_level_values() -> tuple[str, ...]:
    return tuple(dict.fromkeys(ONS_SELECT_GEOGRAPHY_LEVELS.values()))


def geography_identity_from_normalized(
    *,
    target_level: str,
    geography: dict[str, Any] | None,
    fallback_code: str,
) -> dict[str, Any]:
    level = LEVEL_BY_AREA_LEVEL.get(target_level)
    normalized_level = level.area_level if level else target_level
    geography = geography if isinstance(geography, dict) else {}
    code = _clean_text(geography.get("currentCode") or geography.get("code")) or fallback_code
    current_name = _clean_text(geography.get("currentName") or geography.get("name"))
    display_name = _clean_text(geography.get("displayName"))
    name = current_name or display_name or code
    identity: dict[str, Any] = {
        "id": code,
        "level": normalized_level,
        "name": name,
    }
    if current_name:
        identity["currentName"] = current_name
    current_name_welsh = _clean_text(
        geography.get("currentNameWelsh") or geography.get("nameWelsh")
    )
    if current_name_welsh:
        identity["currentNameWelsh"] = current_name_welsh
    if display_name:
        identity["displayName"] = display_name
        identity["preferredDisplayName"] = display_name
    display_name_welsh = _clean_text(geography.get("displayNameWelsh"))
    if display_name_welsh:
        identity["displayNameWelsh"] = display_name_welsh
    source = geography.get("displayNameSource")
    if isinstance(source, dict):
        identity["displayNameSource"] = source
    for field in ("displayNameLocalAuthority", "displayNameType"):
        value = _clean_text(geography.get(field))
        if value:
            identity[field] = value
    status = _clean_text(geography.get("status"))
    if status:
        identity["status"] = status
    source_dataset = _clean_text(geography.get("sourceDataset"))
    if source_dataset:
        identity["sourceDataset"] = source_dataset
    if display_name and current_name and display_name != current_name:
        identity["namePolicy"] = (
            "name/currentName preserve the official ONS/RGC label; displayName is a "
            "non-official disambiguating display label."
        )
    return identity


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None
