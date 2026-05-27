# FaceHealth - AI-Powered Patient Recognition System

FaceHealth is a premium web application built using Python Flask, SQLAlchemy, SQLite, and optional high-accuracy Face Recognition (dlib). It is designed to allow healthcare clinics to recognize patients at checkout or sign-in using their webcam, show their comprehensive treatment history, and allow doctors/admins to update treatments on the fly.

## 🚀 One-Click Deploy to Render

You can deploy this application directly to **Render** completely for free using Docker. Click the button below to start the automatic deployment:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/saran8749/face_web_project)

---

## ✨ Features

- **Webcam Face Scanning**: High-fidelity interface with animated scanlines that captures and recognizes patients in real-time.
- **Auto-Generated Patient IDs**: Automatically formats and increments IDs as `PID-YYYY-NNNNN` on registration.
- **Admin Dashboard**: Comprehensive stats tracking, registration management, report exporting to Excel, and treatment log management.
- **Patient Dashboard**: Dynamic user profile, current treatment metrics, and detailed treatment timelines.
- **Premium Glassmorphism UI**: Beautiful dark theme designed for modern medical facilities with fluid micro-animations.

---

## 🛠️ Local Development

### 1. Prerequisites
Make sure you have Python 3.10+ and `pip` installed.

### 2. Setup
Clone the repository, navigate into the directory, and set up your virtual environment:
```bash
cd face_web_project
pip install -r requirements.txt
```

### 3. Run the App
```bash
py app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.
