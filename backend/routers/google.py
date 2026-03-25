import os
import json
import requests
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

from core.deps import supabase, get_current_user

router = APIRouter(prefix="/api/google", tags=["google"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _get_base_url(request: Request) -> str:
    """Extract the base URL from the incoming request for dynamic redirect."""
    origin = request.headers.get("origin", "")
    if origin:
        return origin.rstrip("/")
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    if forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}".rstrip("/")
    return os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


# ── OAuth Flow ──

@router.get("/connect")
async def google_connect(request: Request, user=Depends(get_current_user)):
    """Start Google OAuth flow - returns authorization URL"""
    # Prefer origin from query param (sent by frontend's window.location.origin)
    frontend_origin = request.query_params.get("origin", "")
    if not frontend_origin:
        frontend_origin = _get_base_url(request)
    redirect_uri = f"{frontend_origin}/api/google/callback"
    state_data = json.dumps({"user_id": user["id"], "origin": frontend_origin})
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state_data,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    return {"authorization_url": url}


@router.get("/callback")
async def google_callback(request: Request, code: str, state: str = ""):
    """Handle Google OAuth callback"""
    # Parse state to get origin and user_id
    try:
        state_data = json.loads(state)
        user_id = state_data.get("user_id", state)
        origin = state_data.get("origin", "")
    except (json.JSONDecodeError, TypeError):
        user_id = state
        origin = ""

    if not origin:
        origin = _get_base_url(request)

    redirect_uri = f"{origin}/api/google/callback"

    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).json()

    if "error" in token_resp:
        return RedirectResponse(f"{origin}/settings?google_error={token_resp.get('error_description', 'OAuth failed')}")

    # Get user email from Google
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token_resp['access_token']}"}
    ).json()

    google_email = userinfo.get("email", "")

    # Save tokens to tenant
    if user_id:
        tenant_result = supabase.table("tenants").select("id, settings").eq("owner_id", user_id).execute()
        if tenant_result.data:
            tenant = tenant_result.data[0]
            settings = tenant.get("settings") or {}
            settings["google_tokens"] = {
                "access_token": token_resp["access_token"],
                "refresh_token": token_resp.get("refresh_token"),
                "token_uri": "https://oauth2.googleapis.com/token",
                "expiry": (datetime.now(timezone.utc) + timedelta(seconds=token_resp.get("expires_in", 3600))).isoformat(),
                "email": google_email,
                "connected_at": datetime.now(timezone.utc).isoformat(),
            }
            supabase.table("tenants").update({"settings": settings}).eq("id", tenant["id"]).execute()

    return RedirectResponse(f"{origin}/settings?google_connected=true")


@router.get("/status")
async def google_status(user=Depends(get_current_user)):
    """Check if Google is connected"""
    tenant_result = supabase.table("tenants").select("settings").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        return {"connected": False}
    settings = tenant_result.data[0].get("settings") or {}
    tokens = settings.get("google_tokens")
    if not tokens or not tokens.get("refresh_token"):
        return {"connected": False}
    return {
        "connected": True,
        "email": tokens.get("email", ""),
        "connected_at": tokens.get("connected_at", ""),
    }


@router.post("/disconnect")
async def google_disconnect(user=Depends(get_current_user)):
    """Disconnect Google account"""
    tenant_result = supabase.table("tenants").select("id, settings").eq("owner_id", user["id"]).execute()
    if tenant_result.data:
        tenant = tenant_result.data[0]
        settings = tenant.get("settings") or {}
        settings.pop("google_tokens", None)
        supabase.table("tenants").update({"settings": settings}).eq("id", tenant["id"]).execute()
    return {"status": "disconnected"}


# ── Helper: Get Google Credentials ──

async def get_google_creds(user_id: str):
    tenant_result = supabase.table("tenants").select("id, settings").eq("owner_id", user_id).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=400, detail="No tenant found")
    settings = tenant_result.data[0].get("settings") or {}
    tokens = settings.get("google_tokens")
    if not tokens or not tokens.get("refresh_token"):
        raise HTTPException(status_code=401, detail="Google not connected. Please connect your Google account first.")

    creds = Credentials(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        tokens["access_token"] = creds.token
        tokens["expiry"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        supabase.table("tenants").update({"settings": {**settings, "google_tokens": tokens}}).eq("id", tenant_result.data[0]["id"]).execute()

    return creds


# ── Calendar Endpoints ──

@router.get("/calendar/list")
async def list_calendars(user=Depends(get_current_user)):
    """List user's Google Calendars"""
    creds = await get_google_creds(user["id"])
    service = build("calendar", "v3", credentials=creds)
    result = service.calendarList().list().execute()
    calendars = result.get("items", [])
    return {"calendars": [{
        "id": c["id"],
        "name": c.get("summary", ""),
        "primary": c.get("primary", False),
        "color": c.get("backgroundColor", ""),
    } for c in calendars]}


class CalendarEventCreate(BaseModel):
    summary: str
    start: str  # ISO datetime
    end: str
    description: Optional[str] = ""
    location: Optional[str] = ""

class CalendarEventUpdate(BaseModel):
    summary: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None


@router.get("/calendar/events")
async def list_calendar_events(user=Depends(get_current_user), max_results: int = 20):
    creds = await get_google_creds(user["id"])
    service = build("calendar", "v3", credentials=creds)
    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(
        calendarId="primary", timeMin=now, maxResults=max_results,
        singleEvents=True, orderBy="startTime"
    ).execute()
    events = result.get("items", [])
    return {"events": [{
        "id": e["id"],
        "summary": e.get("summary", ""),
        "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
        "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date", "")),
        "description": e.get("description", ""),
        "location": e.get("location", ""),
        "status": e.get("status", ""),
    } for e in events]}


@router.post("/calendar/events")
async def create_calendar_event(data: CalendarEventCreate, user=Depends(get_current_user)):
    creds = await get_google_creds(user["id"])
    service = build("calendar", "v3", credentials=creds)
    body = {
        "summary": data.summary,
        "start": {"dateTime": data.start, "timeZone": "UTC"},
        "end": {"dateTime": data.end, "timeZone": "UTC"},
        "description": data.description or "",
        "location": data.location or "",
    }
    event = service.events().insert(calendarId="primary", body=body).execute()
    return {"id": event["id"], "summary": event.get("summary"), "link": event.get("htmlLink")}


@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str, user=Depends(get_current_user)):
    creds = await get_google_creds(user["id"])
    service = build("calendar", "v3", credentials=creds)
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return {"status": "deleted"}


# ── Sheets Endpoints ──

class SheetsReadRequest(BaseModel):
    spreadsheet_id: str
    range: str  # e.g. "Sheet1!A1:D10"

class SheetsWriteRequest(BaseModel):
    spreadsheet_id: str
    range: str
    values: list  # [[row1_col1, row1_col2], [row2_col1, row2_col2]]

class SheetsAppendRequest(BaseModel):
    spreadsheet_id: str
    range: str
    values: list


@router.post("/sheets/read")
async def read_sheet(data: SheetsReadRequest, user=Depends(get_current_user)):
    creds = await get_google_creds(user["id"])
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=data.spreadsheet_id, range=data.range
    ).execute()
    return {"values": result.get("values", []), "range": result.get("range", "")}


@router.post("/sheets/write")
async def write_sheet(data: SheetsWriteRequest, user=Depends(get_current_user)):
    creds = await get_google_creds(user["id"])
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().update(
        spreadsheetId=data.spreadsheet_id, range=data.range,
        valueInputOption="USER_ENTERED", body={"values": data.values}
    ).execute()
    return {"updated_cells": result.get("updatedCells", 0), "updated_range": result.get("updatedRange", "")}


@router.post("/sheets/append")
async def append_sheet(data: SheetsAppendRequest, user=Depends(get_current_user)):
    creds = await get_google_creds(user["id"])
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().append(
        spreadsheetId=data.spreadsheet_id, range=data.range,
        valueInputOption="USER_ENTERED", body={"values": data.values}
    ).execute()
    return {"updated_range": result.get("updates", {}).get("updatedRange", "")}


@router.get("/sheets/list")
async def list_sheets(user=Depends(get_current_user)):
    """List spreadsheets from Google Drive"""
    creds = await get_google_creds(user["id"])
    service = build("drive", "v3", credentials=creds)
    result = service.files().list(
        q="mimeType='application/vnd.google-apps.spreadsheet'",
        fields="files(id, name, modifiedTime)",
        orderBy="modifiedTime desc",
        pageSize=20,
    ).execute()
    return {"sheets": [{"id": f["id"], "name": f["name"], "modified": f.get("modifiedTime", "")} for f in result.get("files", [])]}


# ── Leads Export to Sheets ──

@router.post("/sheets/export-leads")
async def export_leads_to_sheet(user=Depends(get_current_user)):
    """Export all leads to a new Google Sheet"""
    creds = await get_google_creds(user["id"])
    tenant_result = supabase.table("tenants").select("id").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")

    leads = supabase.table("leads").select("*").eq("tenant_id", tenant_result.data[0]["id"]).execute().data or []

    sheets_service = build("sheets", "v4", credentials=creds)

    # Create new spreadsheet
    ss = sheets_service.spreadsheets().create(body={
        "properties": {"title": f"AgentZZ Leads - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"},
        "sheets": [{"properties": {"title": "Leads"}}]
    }).execute()

    # Headers + data
    headers = ["Name", "Email", "Phone", "Stage", "Value", "Temperature", "Source", "Created At"]
    rows = [headers]
    for lead in leads:
        rows.append([
            lead.get("name", ""), lead.get("email", ""), lead.get("phone", ""),
            lead.get("stage", ""), str(lead.get("value", 0)), lead.get("temperature", ""),
            lead.get("source", ""), lead.get("created_at", ""),
        ])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss["spreadsheetId"], range="Leads!A1",
        valueInputOption="USER_ENTERED", body={"values": rows}
    ).execute()

    return {
        "spreadsheet_id": ss["spreadsheetId"],
        "url": ss.get("spreadsheetUrl", f"https://docs.google.com/spreadsheets/d/{ss['spreadsheetId']}"),
        "leads_exported": len(leads),
    }
