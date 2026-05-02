"""Models used by the location/disposal API."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


def _clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_float(value) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_bool(value) -> Optional[bool]:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


@dataclass
class DisposalLocationItem:
    facility_name: str = ""
    address: str = ""
    suburb: str = ""
    postcode: str = ""
    state: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ewaste_category: str = ""
    ewaste_match_text: str = ""
    ewaste_match_column: str = ""
    source: str = ""
    source_file: str = ""
    coord_source: str = ""
    dedupe_key: str = ""
    accepted_items: str = ""
    note: str = ""
    national_phone_number: str = ""
    website_uri: str = ""
    google_maps_uri: str = ""
    business_status: str = ""
    data_quality_status: str = ""
    quality_reason: str = ""
    state_full_name: str = ""
    council: str = ""
    lga_region: str = ""
    region: str = ""
    postcode_latitude: Optional[float] = None
    postcode_longitude: Optional[float] = None

    @classmethod
    def from_row(cls, row: dict) -> "DisposalLocationItem":
        return cls(
            facility_name=_clean_text(row.get("facility_name")),
            address=_clean_text(row.get("address")),
            suburb=_clean_text(row.get("suburb")),
            postcode=_clean_text(row.get("postcode")),
            state=_clean_text(row.get("state")).upper(),
            latitude=_clean_float(row.get("latitude")),
            longitude=_clean_float(row.get("longitude")),
            ewaste_category=_clean_text(row.get("ewaste_category")),
            ewaste_match_text=_clean_text(row.get("ewaste_match_text")),
            ewaste_match_column=_clean_text(row.get("ewaste_match_column")),
            source=_clean_text(row.get("source")),
            source_file=_clean_text(row.get("source_file")),
            coord_source=_clean_text(row.get("coord_source")),
            dedupe_key=_clean_text(row.get("dedupe_key")),
            accepted_items=_clean_text(row.get("accepted_items")),
            note=_clean_text(row.get("note")),
            national_phone_number=_clean_text(row.get("national_phone_number")),
            website_uri=_clean_text(row.get("website_uri")),
            google_maps_uri=_clean_text(row.get("google_maps_uri")),
            business_status=_clean_text(row.get("business_status")),
            data_quality_status=_clean_text(row.get("data_quality_status")),
            quality_reason=_clean_text(row.get("quality_reason")),
            state_full_name=_clean_text(row.get("state_full_name")),
            council=_clean_text(row.get("council")),
            lga_region=_clean_text(row.get("lga_region")),
            region=_clean_text(row.get("region")),
            postcode_latitude=_clean_float(row.get("postcode_latitude")),
            postcode_longitude=_clean_float(row.get("postcode_longitude")),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LocationLookupRow:
    state_code: str
    state_name: str
    council: str
    suburb: str
    postcode: str

    @classmethod
    def from_row(cls, row: dict) -> "LocationLookupRow":
        return cls(
            state_code=_clean_text(row.get("state_code")).upper(),
            state_name=_clean_text(row.get("state_name")),
            council=_clean_text(row.get("council")),
            suburb=_clean_text(row.get("suburb")),
            postcode=_clean_text(row.get("postcode")),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PostcodeRow:
    postcode: str
    locality: str
    state: str
    long: Optional[float] = None
    lat: Optional[float] = None
    region: str = ""
    lat_precise: Optional[float] = None
    long_precise: Optional[float] = None
    lgaregion: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "PostcodeRow":
        return cls(
            postcode=_clean_text(row.get("postcode")),
            locality=_clean_text(row.get("locality")),
            state=_clean_text(row.get("state")).upper(),
            long=_clean_float(row.get("long")),
            lat=_clean_float(row.get("lat")),
            region=_clean_text(row.get("region")),
            lat_precise=_clean_float(row.get("lat_precise")),
            long_precise=_clean_float(row.get("long_precise")),
            lgaregion=_clean_text(row.get("lgaregion")),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LocationProfile:
    key: str
    label: str
    state: str
    tier: str
    match_type: str
    aliases: set[str] = field(default_factory=set)
    suburbs: set[str] = field(default_factory=set)
    councils: set[str] = field(default_factory=set)
    postcodes: set[str] = field(default_factory=set)
    points: list[dict] = field(default_factory=list)
    bounds: dict | None = None
    center: dict | None = None

    def to_focus_area(self) -> dict:
        return {
            "label": self.label,
            "tier": self.tier,
            "bounds": self.bounds,
            "center": self.center,
        }

