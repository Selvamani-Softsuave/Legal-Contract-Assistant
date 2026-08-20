"""
Run this once after starting Docker services to:
  1. Create the LegalContractRAG database
  2. Run all Alembic migrations (create all tables)

Usage:
  cd E:\Selvamani\Learning\AI Learning\legal-contract-rag
  python backend/scripts/init_db.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pyodbc
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mssql+pyodbc://sa:LegalRAG_Password2026!@127.0.0.1:1433/LegalContractRAG?driver=ODBC+Driver+17+for+SQL+Server"
)

import re
match = re.search(r'@([^/]+)/([^?]+)', DATABASE_URL)
if not match:
    print("ERROR: Could not parse DATABASE_URL")
    sys.exit(1)

server = match.group(1).replace(':', ',')
db_name = match.group(2)
driver = "ODBC Driver 17 for SQL Server"

print(f"==> Connecting to SQL Server at {server}...")
try:
    conn = pyodbc.connect(
        f"DRIVER={{{driver}}};SERVER={server};DATABASE=master;UID=sa;PWD=LegalRAG_Password2026!;TrustServerCertificate=yes",
        autocommit=True
    )
    cursor = conn.cursor()
    cursor.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{db_name}') CREATE DATABASE [{db_name}]")
    conn.close()
    print(f"==> Database [{db_name}] is ready.")
except Exception as e:
    print(f"ERROR: Could not connect to SQL Server: {e}")
    sys.exit(1)

print("==> Running Alembic migrations...")
import subprocess
result = subprocess.run(
    ["alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
    cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')),
    capture_output=False
)

if result.returncode == 0:
    print("==> All tables created successfully!")
else:
    print("ERROR: Alembic migration failed.")
    sys.exit(1)
