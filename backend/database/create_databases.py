import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

def create_dbs():
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)
    
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    default_db = os.environ.get("POSTGRES_DB", "postgres")
    
    target_dbs = ["sbi_db", "axis_db", "iob_db"]
    
    print(f"Connecting to PostgreSQL at {host}:{port}...")
    
    try:
        conn = psycopg2.connect(dbname=default_db, user=user, password=password, host=host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        for db in target_dbs:
            cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db}'")
            if not cursor.fetchone():
                cursor.execute(f"CREATE DATABASE {db}")
                print(f"✅ Created database: {db}")
            else:
                print(f"⚠️ Database '{db}' already exists.")
                
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to create databases: {e}")
        return

    # Execute schema.sql for each DB
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    for db in target_dbs:
        try:
            conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            print(f"✅ Executed schema.sql on {db}")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Failed to execute schema on {db}: {e}")

if __name__ == "__main__":
    create_dbs()
