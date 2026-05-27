
import os
import io
import json
import base64
from datetime import datetime, date
from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import pandas as pd
import numpy as np

# optional face_recognition
try:
    import face_recognition
    FACE_AVAILABLE = True
except Exception:
    FACE_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_PATH = "sqlite:///database.db"
Base = declarative_base()

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)  # admin or patient
    patient_id = Column(String, nullable=True)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    patient_id = Column(String, unique=True)
    name = Column(String)
    dob = Column(String)
    address = Column(String)
    blood_group = Column(String)
    phone = Column(String)
    encoding = Column(Text, nullable=True)
    image_filename = Column(String, nullable=True)
    treatments = relationship("Treatment", back_populates="patient")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    patient_id = Column(String)
    name = Column(String)
    timestamp = Column(DateTime)
    encoding = Column(Text)
    image_filename = Column(String)
    report_date = Column(Date)

class Treatment(Base):
    __tablename__ = "treatments"
    id = Column(Integer, primary_key=True)
    patient_db_id = Column(Integer, ForeignKey("patients.id"))
    date = Column(Date)
    diagnosis = Column(Text)
    prescription = Column(Text)
    doctor_name = Column(String)
    notes = Column(Text, nullable=True)
    patient = relationship("Patient", back_populates="treatments")

Base.metadata.create_all(engine)

# create default admin if not exists
if not db.query(User).filter_by(username="admin").first():
    admin = User(username="admin", password="admin123", role="admin")
    db.add(admin)
    db.commit()

app = Flask(__name__)
app.secret_key = "change_this_secret"

# helpers
def save_image_from_base64(b64_string, prefix="capture"):
    header, encoded = b64_string.split(",", 1) if "," in b64_string else (None, b64_string)
    data = base64.b64decode(encoded)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = secure_filename(f"{prefix}_{ts}.jpg")
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path, filename

def encoding_from_image_file(path):
    if not FACE_AVAILABLE:
        return None
    img = face_recognition.load_image_file(path)
    encs = face_recognition.face_encodings(img)
    return encs[0] if encs else None

def load_all_patient_encodings():
    patients = db.query(Patient).all()
    encs = []
    ids = []
    for p in patients:
        if p.encoding:
            encs.append(np.array(json.loads(p.encoding)))
            ids.append(p.patient_id)
    return encs, ids

def generate_patient_id():
    """Generate next Patient ID in format PID-YYYY-NNNNN"""
    year = datetime.now().strftime("%Y")
    prefix = f"PID-{year}-"
    # find the highest existing ID with this prefix
    patients = db.query(Patient).filter(Patient.patient_id.like(f"{prefix}%")).all()
    max_num = 0
    for p in patients:
        try:
            num = int(p.patient_id.replace(prefix, ""))
            if num > max_num:
                max_num = num
        except ValueError:
            pass
    return f"{prefix}{max_num + 1:05d}"

# routes
@app.route("/")
def root():
    if "user" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("patient_dashboard"))
    return render_template("home.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/api/next-patient-id")
def next_patient_id():
    return jsonify({"patient_id": generate_patient_id()})

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = db.query(User).filter_by(username=username, password=password).first()
        if user:
            session["user"] = user.username
            session["role"] = user.role
            session["patient_id"] = user.patient_id
            flash("Logged in", "success")
            if user.role=="admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("patient_dashboard"))
        flash("Invalid credentials", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("home"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Admin access required", "error")
        return redirect(url_for("login"))
    patients = db.query(Patient).order_by(Patient.name).all()
    reports = db.query(Report).order_by(Report.timestamp.desc()).limit(200).all()
    return render_template("admin_dashboard.html", patients=patients, reports=reports)

@app.route("/patient/dashboard")
def patient_dashboard():
    if session.get("role") != "patient":
        flash("Patient access required", "error")
        return redirect(url_for("login"))
    pid = session.get("patient_id")
    patient = db.query(Patient).filter_by(patient_id=pid).first()
    reports = db.query(Report).filter_by(patient_id=pid).order_by(Report.timestamp.desc()).all()
    treatments = db.query(Treatment).filter_by(patient_db_id=patient.id).order_by(Treatment.date.desc()).all() if patient else []
    return render_template("patient_dashboard.html", patient=patient, reports=reports, treatments=treatments)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        pid = request.form.get("patient_id","").strip()
        name = request.form.get("name","").strip()
        dob = request.form.get("dob","").strip()
        address = request.form.get("address","").strip()
        blood = request.form.get("blood_group","").strip()
        phone = request.form.get("phone","").strip()
        file = request.files.get("photo")
        if not (pid and name and file):
            flash("patient_id, name and photo required", "error")
            return redirect(url_for("register"))
        filename = secure_filename(f"{pid}_{file.filename}")
        path = os.path.join(UPLOAD_DIR, filename)
        file.save(path)
        enc = encoding_from_image_file(path)
        if FACE_AVAILABLE and enc is None:
            os.remove(path)
            flash("No face detected. Use a clear frontal photo.", "error")
            return redirect(url_for("register"))
        existing = db.query(Patient).filter_by(patient_id=pid).first()
        if existing:
            existing.name=name; existing.dob=dob; existing.address=address
            existing.blood_group=blood; existing.phone=phone
            existing.encoding=json.dumps(enc.tolist()) if enc is not None else None
            existing.image_filename=filename
        else:
            p = Patient(patient_id=pid, name=name, dob=dob, address=address,
                        blood_group=blood, phone=phone,
                        encoding=json.dumps(enc.tolist()) if enc is not None else None,
                        image_filename=filename)
            db.add(p)
            u = User(username=pid, password=dob or "patient123", role="patient", patient_id=pid)
            db.add(u)
        db.commit()
        flash("Patient registered successfully! Sign in with your Patient ID and Date of Birth as password.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/scan")
def scan():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("scan.html")

@app.route("/recognize", methods=["POST"])
def recognize():
    if "user" not in session:
        return jsonify({"status":"error","message":"login required"}),401
    data = request.json
    image_b64 = data.get("image")
    if not image_b64:
        return jsonify({"status":"error","message":"no image"}),400
    path, filename = save_image_from_base64(image_b64)
    enc = encoding_from_image_file(path) if FACE_AVAILABLE else None
    if FACE_AVAILABLE and enc is None:
        return jsonify({"status":"no_face"})
    patients = db.query(Patient).all()
    known_encs=[]; ids=[]
    for p in patients:
        if p.encoding:
            known_encs.append(np.array(json.loads(p.encoding)))
            ids.append(p.patient_id)
    name="Unknown"; pid="Unknown"
    if known_encs and FACE_AVAILABLE:
        distances = face_recognition.face_distance(known_encs, enc)
        best = int(np.argmin(distances))
        if float(distances[best]) < 0.5:
            pid = ids[best]
            patient = db.query(Patient).filter_by(patient_id=pid).first()
            name = patient.name
    report = Report(patient_id=pid, name=name, timestamp=datetime.now(),
                    encoding=json.dumps(enc.tolist()) if enc is not None else None,
                    image_filename=filename, report_date=date.today())
    db.add(report); db.commit()
    return jsonify({"status":"ok","name":name,"matched": name!="Unknown"})

@app.route("/patient/<string:patient_id>/treatments")
def view_treatments(patient_id):
    role = session.get("role")
    if role != "admin" and session.get("patient_id") != patient_id:
        flash("Access denied", "error")
        return redirect(url_for("login"))
    patient = db.query(Patient).filter_by(patient_id=patient_id).first()
    if not patient:
        flash("Patient not found", "error")
        return redirect(url_for("admin_dashboard"))
    treatments = db.query(Treatment).filter_by(patient_db_id=patient.id).order_by(Treatment.date.desc()).all()
    return render_template("treatments.html", patient=patient, treatments=treatments)

@app.route("/patient/<string:patient_id>/treatments/add", methods=["GET","POST"])
def add_treatment(patient_id):
    if session.get("role") != "admin":
        flash("Admin required to add treatment", "error")
        return redirect(url_for("login"))
    patient = db.query(Patient).filter_by(patient_id=patient_id).first()
    if not patient:
        flash("Patient not found", "error")
        return redirect(url_for("admin_dashboard"))
    if request.method=="POST":
        date_s = request.form.get("date")
        diag = request.form.get("diagnosis")
        pres = request.form.get("prescription")
        doctor = request.form.get("doctor_name")
        notes = request.form.get("notes")
        try:
            dt = datetime.strptime(date_s, "%Y-%m-%d").date()
        except Exception:
            dt = date.today()
        t = Treatment(patient_db_id=patient.id, date=dt, diagnosis=diag, prescription=pres, doctor_name=doctor, notes=notes)
        db.add(t); db.commit()
        flash("Treatment added", "success")
        return redirect(url_for("view_treatments", patient_id=patient_id))
    return render_template("add_treatment.html", patient=patient)

@app.route("/treatment/<int:treatment_id>/delete", methods=["POST"])
def delete_treatment(treatment_id):
    if session.get("role") != "admin":
        flash("Admin required to delete treatment", "error")
        return redirect(url_for("login"))
    treatment = db.query(Treatment).filter_by(id=treatment_id).first()
    if not treatment:
        flash("Treatment not found", "error")
        return redirect(url_for("admin_dashboard"))
    patient = db.query(Patient).filter_by(id=treatment.patient_db_id).first()
    pid = patient.patient_id if patient else None
    db.delete(treatment)
    db.commit()
    flash("Treatment deleted", "success")
    if pid:
        return redirect(url_for("view_treatments", patient_id=pid))
    return redirect(url_for("admin_dashboard"))

@app.route("/export")
def export_reports():
    if session.get("role") != "admin":
        flash("Admin required", "error")
        return redirect(url_for("login"))
    rows = db.query(Report).order_by(Report.timestamp.desc()).all()
    data=[]
    for r in rows:
        data.append({"Patient ID":r.patient_id,"Name":r.name,"Timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else ""})
    df = pd.DataFrame(data)
    buf = io.BytesIO(); df.to_excel(buf, index=False); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="reports.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__=="__main__":
    app.run(debug=True)
