import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Base paths ---
BASE_DIR = Path(os.getenv("BASE_OUTPUT_DIR"))
MANIFESTS_DIR = BASE_DIR / "manifests"
LOGS_DIR = BASE_DIR / "logs"

# --- Output directories ---
EPA_PAGES_DIR = BASE_DIR / "epa-pages"
EPA_FILES_DIR = BASE_DIR / "epa-files"
FTP_DIR = BASE_DIR / "ftp-mirror"
AGOL_DIR = BASE_DIR / "agol-layers"

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

# --- Harvard Dataverse ---
DATAVERSE_BASE_URL = "https://dataverse.harvard.edu/api"
DATAVERSE_TOKEN = os.getenv("DATAVERSE_TOKEN")
DATAVERSE_ALIAS = os.getenv("DATAVERSE_ALIAS")


def init_dirs():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
