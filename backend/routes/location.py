"""Location/disposal endpoints."""

from __future__ import annotations

from flask import Blueprint, request

from routes.login import login_required
from services.location_service import search_disposal_locations
from utils.helpers import fail, ok


location_bp = Blueprint("location", __name__)


@location_bp.route("/map/disposal-locations", methods=["GET"])
@login_required
def search_all_disposal_locations():
    try:
        payload = search_disposal_locations(
            search_text=request.args.get("searchText", ""),
            search_range=request.args.get("searchRange", "exact"),
        )
        return ok(payload["items"], meta=payload["meta"])
    except Exception as exc:
        return fail(f"Database error: {exc}", 503)

