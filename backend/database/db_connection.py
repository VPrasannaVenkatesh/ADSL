import os
import psycopg2
from dotenv import load_dotenv

def get_connection(bank_name):
    """
    Returns a psycopg2 connection for the specified bank database.
    bank_name should be one of: 'SBI', 'AXIS', 'IOB'
    """
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)
    
    url_env_var = f"{bank_name.upper()}_DATABASE_URL"
    db_url = os.environ.get(url_env_var)
    
    if not db_url:
        raise ValueError(f"Environment variable {url_env_var} is not set.")
        
    return psycopg2.connect(db_url)
