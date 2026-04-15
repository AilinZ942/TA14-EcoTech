from azure.functions import FunctionApp, HttpRequest, HttpResponse, SqlRowList, AuthLevel
import json
import logging

app = FunctionApp(http_auth_level=AuthLevel.ANONYMOUS)
logger = logging.getLogger(__name__)

# Helper functions

def _safe_strip(value):
    if value is None:
        return ""
    return str(value).strip()


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


# Location function


@app.function_name(name="GetPerson")
@app.route(route="getperson")
@app.sql_input(arg_name="person",
                        command_text="select [ID], [FirstName], [LastName] from dbo.Persons",
                        command_type="Text",
                        connection_string_setting="SqlConnectionString")
def get_person(req: HttpRequest, person: SqlRowList) -> HttpResponse:
    rows = list(map(lambda r: json.loads(r.to_json()), person))
    

    return HttpResponse(
        json.dumps(rows),
        status_code=200,
        mimetype="application/json"
    )


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
    for row in rows:
        print(row)
    items = [_row_to_disposal_item(row) for row in rows]



    response_body = {
        "items": items,
        "meta": {
            "pipeline": "azure",
            "source": "api",
        },
    }

    logger.info("Returning %s disposal locations for postcode %s", len(items), postcode)

    return HttpResponse(
        json.dumps(response_body),
        status_code=200,
        mimetype="application/json",
    )
