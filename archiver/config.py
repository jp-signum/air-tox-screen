import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Base paths ---
BASE_DIR = Path(os.getenv("BASE_OUTPUT_DIR"))
PHASE_DIRS = {
    0: BASE_DIR / "phase0_manifest",
    1: BASE_DIR / "phase1_docs",
    2: BASE_DIR / "phase2_static",
    3: BASE_DIR / "phase3_ftp",
    4: BASE_DIR / "phase4_arcgis",
    5: BASE_DIR / "phase5_visual",
    6: BASE_DIR / "phase6_upload",
}
LOGS_DIR = BASE_DIR / "logs"

# --- EPA ---
EPA_BASE_URL = "https://www.epa.gov"
EPA_AIRTOXSCREEN_URL = f"{EPA_BASE_URL}/AirToxScreen"
EPA_RESULTS_URL = f"{EPA_AIRTOXSCREEN_URL}/2020-airtoxscreen-assessment-results"
EPA_FTP_URL = "gaftp.epa.gov"
EPA_FTP_PATH = "/rtrmodeling_public/AirToxScreen/2020/"

# --- ArcGIS ---
AGOL_REST_BASE = "https://www.arcgis.com/sharing/rest"
AGOL_ITEM_2020 = "a0deb771dbcd40d0a46fbe83adc51747"
AGOL_ITEM_2017 = "a2eea9c204004158a85a18371d6883bc"
ARCGIS_PAGE_SIZE = 2000

# --- Zenodo ---
ZENODO_BASE_URL = "https://zenodo.org/api"
ZENODO_TOKEN = os.getenv("ZENODO_TOKEN")

# --- Ensure output dirs exist ---


def init_dirs():
    for d in PHASE_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
