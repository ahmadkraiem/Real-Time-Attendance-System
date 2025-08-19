# Real-Time Attendance (Python 3.8.10)

This repo is ready-to-run and **GitHub-ready**. It includes a prebuilt `dlib` wheel to avoid face_recognition install issues.

## Quick Start (Windows PowerShell)
```powershell
git clone <repo-url>
cd <repo-folder>
.\setup.ps1
.\.venv\Scripts\Activate.ps1
copy .env.example .env   # then edit your secrets
streamlit run Home.py
```

## Quick Start (Linux/macOS)
```bash
git clone <repo-url>
cd <repo-folder>
chmod +x setup.sh && ./setup.sh
source .venv/bin/activate
cp .env.example .env     # then edit your secrets
streamlit run Home.py
```

## Notes
- We **install dlib from a local wheel**: `wheels/dlib-19.22.99-cp38-cp38-win_amd64.whl` before installing the rest of requirements.
- Requirements pinned for Python 3.8 in `requirements-py38.txt`.
- `.env.example` is provided; duplicate it to `.env` and fill in your email credentials (never commit `.env`).

## ⚠️ Windows PowerShell Note

If you face an error when activating the virtual environment on Windows (for example when running `.\venv\Scripts\Activate.ps1`), it may be caused by PowerShell execution policies.

To fix this, you can run the following command in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
## Privacy
The repo ignores personal data by default: database files, encodings, and dataset images are not committed (see `.gitignore`).
