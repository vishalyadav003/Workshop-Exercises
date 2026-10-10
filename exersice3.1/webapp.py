"""Web dashboard for the SQLite equipment maintenance database."""
from flask import Flask, jsonify, render_template, request
from database import DatabaseManager, seed_database, REQUEST_STATUSES, EQUIPMENT_STATUSES
import os
from pathlib import Path

app = Flask(__name__)

def db_open():
    db = DatabaseManager(os.environ.get("MAINTENANCE_DB_PATH", str(Path(__file__).with_name("maintenance.db"))))
    db.create_schema(); seed_database(db); return db

def state():
    with db_open() as db:
        requests = db.connection.execute("""SELECT r.*,e.name AS equipment_name,e.location,t.name AS technician_name
          FROM service_requests r JOIN equipment e ON e.id=r.equipment_id LEFT JOIN technicians t ON t.id=r.technician_id ORDER BY r.id DESC""").fetchall()
        equipment = db.connection.execute("SELECT * FROM equipment ORDER BY id").fetchall()
        techs = db.connection.execute("SELECT * FROM technicians ORDER BY name").fetchall()
        updates = db.connection.execute("""SELECT u.*,r.issue_description,e.name AS equipment_name FROM service_updates u JOIN service_requests r ON r.id=u.request_id JOIN equipment e ON e.id=r.equipment_id ORDER BY u.id DESC LIMIT 8""").fetchall()
        return {"requests":[dict(x) for x in requests],"equipment":[dict(x) for x in equipment],"technicians":[dict(x) for x in techs],"updates":[dict(x) for x in updates],"counts":db.count_requests_by_status(),"overdue":len(db.list_overdue_requests()),"avg_hours":db.average_resolution_hours(),"repeated":db.repeated_faults(),"costs":db.monthly_maintenance_costs(),"statuses":REQUEST_STATUSES,"equipment_statuses":EQUIPMENT_STATUSES}

@app.get("/")
def index(): return render_template("index.html")

@app.get("/api/state")
def api_state(): return jsonify(state())

@app.post("/api/requests")
def create_request():
    data=request.get_json(silent=True) or {}
    try:
        with db_open() as db: rid=db.create_request(int(data["equipment_id"]),data["issue_description"],int(data["technician_id"]) if data.get("technician_id") else None)
        return jsonify(message=f"Request #{rid} created.",state=state()),201
    except (ValueError,KeyError,TypeError) as exc: return jsonify(error=str(exc)),400

@app.post("/api/equipment")
def create_equipment():
    data=request.get_json(silent=True) or {}
    try:
        with db_open() as db: eid=db.add_equipment(data.get("name",""),data.get("category",""),data.get("location",""),data.get("status","Operational"))
        return jsonify(message=f"Equipment #{eid} added.",state=state()),201
    except (ValueError,KeyError,TypeError) as exc: return jsonify(error=str(exc)),400

@app.patch("/api/requests/<int:rid>")
def update_request(rid):
    data=request.get_json(silent=True) or {}
    try:
        with db_open() as db: db.update_request_status(rid,data.get("status",""),data.get("notes",""))
        return jsonify(message="Request updated and activity recorded.",state=state())
    except (ValueError,LookupError) as exc: return jsonify(error=str(exc)),400

@app.post("/api/requests/<int:rid>/updates")
def add_update(rid):
    data=request.get_json(silent=True) or {}
    try:
        with db_open() as db: db.add_update(rid,data.get("notes",""),float(data.get("cost",0)))
        return jsonify(message="Service note saved.",state=state()),201
    except (ValueError,LookupError,TypeError) as exc: return jsonify(error=str(exc)),400

if __name__ == "__main__": app.run(host="127.0.0.1",debug=False,port=5301)
