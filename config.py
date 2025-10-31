from dotenv import load_dotenv
import os, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv()
    
DATABASE_NAME = os.getenv("DATABASE_NAME", "default_database")
DATABASE_USER = os.getenv("DATABASE_USER", "default_user")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "default_password")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")

SMTP_USER = os.getenv("SMTP_USER", "default_smtp_user")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "default_smtp_password")

APP_BASE_URL = "http://localhost:5000"

# --- Configurazione API cambio valuta ---
EXCHANGE_API_URL = "https://openexchangerates.org/api"
EXCHANGE_API_KEY = "35fe9e8c93634d9fa3f4e4b9374388a2"
