# Field Data Analysis and Automated Feature Validation

This project lets a user upload a field image, detect traffic signs with a trained YOLOv8 model, extract text with Tesseract OCR, and review the result in a browser-based dashboard.

## What is included

- FastAPI backend for image upload and inference
- YOLOv8 pipeline using `app/models/best.pt`
- OCR extraction with Tesseract
- Vanilla HTML, CSS, and JavaScript frontend
- Dockerfile for deployment
- Render blueprint file at the repository root

## Project layout

```text
app/
├── main.py
├── ai_pipeline.py
├── models/
│   └── best.pt
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── uploads/
├── requirements.txt
├── Dockerfile
└── render.yaml
```

## Local development

### 1. Install Python dependencies

From the repository root:

```powershell
cd app
python -m pip install -r requirements.txt
```

If you are using your existing local environment:

```powershell
env\Scripts\python.exe -m pip install -r app\requirements.txt
```

### 2. Install Tesseract locally

OCR requires the Tesseract executable to be installed on your machine.

- If `tesseract` is on your `PATH`, the app will detect it automatically.
- If it is installed in a custom location, set `TESSERACT_CMD` before starting the app.

Example:

```powershell
$env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 3. Start the FastAPI app

```powershell
cd app
uvicorn main:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Deployment on Render

This repository includes a root-level `render.yaml` so you can deploy the `app/` directory as a Docker web service.

### Deployment steps

1. Push this repository to GitHub.
2. In Render, create a new Blueprint or Web Service from that repository.
3. Render will build `app/Dockerfile`.
4. The health check endpoint is `/api/health`.

The Docker image installs Tesseract automatically, so OCR works in deployment without extra manual setup.

## GitHub push workflow

If this folder is not already a Git repository:

```powershell
git init -b main
git add .
git commit -m "Initial traffic sign analysis web app"
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Important note about large files

The root `.gitignore` keeps large training assets local:

- `GTSRB_Final_Training_Images/`
- `GTSRB_Final_Training_Images.zip`
- `datasets/`
- `runs/`
- `env/`

This keeps the GitHub repository lightweight while preserving the deployable app and trained model.
