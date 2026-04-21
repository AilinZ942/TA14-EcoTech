from azure.functions import FunctionApp, HttpRequest, HttpResponse, SqlRowList, AuthLevel
import json
import logging

# Create the FunctionApp instance, authentication level is set to anonymous for simplicity, adjust as needed for production
app = FunctionApp(http_auth_level=AuthLevel.ANONYMOUS)
logger = logging.getLogger(__name__)

# Helper functions

# A helper function to safely strip string values, returning an empty string if the value is None
def _safe_strip(value):
    if value is None:
        return ""
    return str(value).strip()

# A helper function to convert a SQL row to a disposal item dictionary, handling potential None values and ensuring proper types
def _row_to_disposal_item(row):
    return {
        "facility_name": _safe_strip(row.get("facility_name")),
        "address": _safe_strip(row.get("address")),
        "suburb": _safe_strip(row.get("suburb")),
        "postcode": _safe_strip(row.get("postcode")),
        "state": _safe_strip(row.get("state")),
        "latitude": float(row["latitude"]) if row.get("latitude") is not None else None,
        "longitude": float(row["longitude"]) if row.get("longitude") is not None else None,
    }






# Used for iteration 2 - search by postcode, returns all locations in that postcode
@app.function_name(name="SearchDisposalLocations")
@app.route(route="map/disposal-locations/{postcode}")
@app.sql_input(
    arg_name="ewaste_rows",
    command_text="""
        SELECT
            facility_name,
            address,
            suburb,
            postcode,
            state,
            latitude,
            longitude
        FROM dbo.clean_ewaste_facilities_geocoded
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND postcode = @postcode
    """,
    command_type="Text",
    parameters="@postcode={postcode}",
    connection_string_setting="SqlConnectionString",
)
def search_disposal_locations(req: HttpRequest, ewaste_rows: SqlRowList) -> HttpResponse:
    postcode = _safe_strip(req.route_params.get("postcode"))

    
    if not postcode:
        return HttpResponse(
            json.dumps({"error": "postcode is required."}),
            status_code=400,
            mimetype="application/json",
        )

    rows = [json.loads(row.to_json()) for row in ewaste_rows]
    items = [_row_to_disposal_item(row) for row in rows]

    logger.info("Returning %s disposal locations for postcode %s", len(items), postcode)

    return HttpResponse(
        json.dumps({
            "items": items,
            "meta": {
                "pipeline": "azure",
                "source": "api",
            },
        }),
        status_code=200,
        mimetype="application/json",
    )


# Used for iteration 1 - returns all locations, no filtering, this is the original function we had before we added the postcode filter, we can keep it for testing and comparison purposes
@app.function_name(name="SearchAllDisposalLocations")
@app.route(route="map/disposal-locations/search", methods=["POST"])
@app.sql_input(
    arg_name="ewaste_rows",
    command_text="""
        SELECT
            facility_name,
            address,
            suburb,
            postcode,
            state,
            latitude,
            longitude
        FROM dbo.clean_ewaste_facilities_geocoded
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY suburb, facility_name
    """,
    command_type="Text",
    connection_string_setting="SqlConnectionString",
)
def search_all_disposal_locations(req: HttpRequest, ewaste_rows: SqlRowList) -> HttpResponse:

   
    rows = [json.loads(row.to_json()) for row in ewaste_rows]
    items = [_row_to_disposal_item(row) for row in rows]


    return HttpResponse(
        json.dumps({
            "items": items,
            "meta": {
                "pipeline": "azure",
                "source": "sql-db",
            },
        }),
        status_code=200,
        mimetype="application/json",
    )
