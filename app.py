from uuid import uuid4
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from random_string_generator import generate
from create_report import generate_report
from reports import reports

app = FastAPI()

@app.get("/trigger_report")
def trigger_report(background_tasks: BackgroundTasks):
    report_id = uuid4().hex
    reports[report_id] = {"status": "Running", "csv_path": None}
    background_tasks.add_task(generate_report, report_id)
    return {"report_id": report_id}

@app.get("/get_report/")
def get_report(report_id: str):
    report = reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["status"] == "Running":
        return {"status": "Running"}
    if report["csv_path"] is None:
        raise HTTPException(status_code=500, detail="CSV path not ready")

    return FileResponse(report["csv_path"], media_type="text/csv", filename=f"{report_id}.csv")

