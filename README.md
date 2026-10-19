# IF3170_G29_TheSeekers

## Repository structure

```text
.
|-- src/
|   |-- backend/     Python algorithms, core domain, CLI, and Flask API
|   `-- frontend/    React dashboard
|-- docs/            Final report and supporting documentation
|-- requirements.txt
`-- README.md
```

## Setup

Run these commands from the repository root:

```powershell
python -m pip install -r requirements.txt
cd src/frontend
npm ci
npm run build
cd ../..
```

## Run dashboard

```powershell
python -m src.backend.server
```

Open `http://127.0.0.1:8000`.

## Run terminal application

```powershell
python -m src.backend.main
```
