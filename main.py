from fastapi import FastAPI, UploadFile, File, Request
from pydantic import BaseModel
from datetime import datetime
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="FieldLog API")

# In-memory DB (temporary)
fake_db = {
    "shifts": []
}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --------- MODELS ---------

class StartShiftRequest(BaseModel):
    username: str
    assignment_name: str
    start_latitude: float
    start_longitude: float

class ShiftNoteRequest(BaseModel):
    text: str

class EndShiftRequest(BaseModel):
    end_latitude: float
    end_longitude: float


# --------- ROUTES ---------

@app.post("/shifts/{shift_id}/end")
def end_shift(shift_id: int, data: EndShiftRequest):
    for shift in fake_db["shifts"]:
        if shift["id"] == shift_id:
            shift["end_time"] = datetime.utcnow().isoformat()
            shift["end_latitude"] = data.end_latitude
            shift["end_longitude"] = data.end_longitude
            shift["status"] = "completed"
            return shift
    return {"error": "Shift not found"}


@app.get("/")
def root():
    return {"message": "FieldLog API is running"}

# Start Shift
@app.post("/shifts/start")
def start_shift(data: StartShiftRequest):
    shift = {
        "id": len(fake_db["shifts"]) + 1,
        "username": data.username,
        "assignment_name": data.assignment_name,
        "start_time": datetime.utcnow().isoformat(),
        "start_latitude": data.start_latitude,
        "start_longitude": data.start_longitude,
        "status": "active",
        "notes": [],
        "photos": []
    }
    fake_db["shifts"].append(shift)
    return shift

# Get Active Shifts
@app.get("/shifts/active")
def get_active_shifts():
    return [s for s in fake_db["shifts"] if s["status"] == "active"]

# Add Note
@app.post("/shifts/{shift_id}/notes")
def add_note(shift_id: int, data: ShiftNoteRequest):
    for shift in fake_db["shifts"]:
        if shift["id"] == shift_id:
            note = {
                "text": data.text,
                "created_at": datetime.utcnow().isoformat()
            }
            shift["notes"].append(note)
            return note
    return {"error": "Shift not found"}

@app.post("/shifts/{shift_id}/photos")
async def upload_photo(shift_id: int, request: Request, file: UploadFile = File(...)):
    for shift in fake_db["shifts"]:
        if shift["id"] == shift_id:
            file_location = f"{UPLOAD_DIR}/shift_{shift_id}_{file.filename}"

            with open(file_location, "wb") as f:
                content = await file.read()
                f.write(content)

            base_url = str(request.base_url).rstrip("/")

            photo = {
                "file_path": file_location,
                "url": f"{base_url}/{file_location}",
                "filename": file.filename,
                "uploaded_at": datetime.utcnow().isoformat()
            }

            shift["photos"].append(photo)
            return photo

    return {"error": "Shift not found"}

# Owner Dashboard
@app.get("/owner/dashboard")
def owner_dashboard():
    active_shifts = [s for s in fake_db["shifts"] if s["status"] == "active"]

    return {
        "active_shifts": active_shifts
    }