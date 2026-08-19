#!/bin/bash
set -e

echo "==> Waiting for SQL Server to be ready..."
for i in $(seq 1 30); do
    if python -c "
import pyodbc, os, sys
conn_str = os.environ.get('DATABASE_URL', '')
# Extract server from URL: mssql+pyodbc://user:pass@server:port/db?...
import re
match = re.search(r'@([^/]+)/([^?]+)', conn_str)
if not match:
    sys.exit(1)
server = match.group(1)
db     = match.group(2)
driver = 'ODBC Driver 17 for SQL Server'
try:
    # Connect to master first (DB may not exist yet)
    conn = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE=master;UID=sa;PWD=LegalRAG_Password2026!;TrustServerCertificate=yes', timeout=3)
    conn.close()
    print('SQL Server is up.')
except Exception as e:
    print(f'Not ready: {e}')
    sys.exit(1)
" 2>/dev/null; then
        break
    fi
    echo "   Attempt $i/30 — SQL Server not ready yet, waiting 3s..."
    sleep 3
done

echo "==> Creating database if it does not exist..."
python -c "
import pyodbc, os, re

conn_str = os.environ.get('DATABASE_URL', '')
match = re.search(r'@([^/]+)/([^?]+)', conn_str)
server = match.group(1)
db     = match.group(2)
driver = 'ODBC Driver 17 for SQL Server'

conn = pyodbc.connect(
    f'DRIVER={{{driver}}};SERVER={server};DATABASE=master;UID=sa;PWD=LegalRAG_Password2026!;TrustServerCertificate=yes',
    autocommit=True
)
cursor = conn.cursor()
cursor.execute(f\"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{db}') CREATE DATABASE [{db}]\")
conn.close()
print(f'Database [{db}] is ready.')
"

echo "==> Running Alembic migrations..."
cd /app
alembic upgrade head

echo "==> Starting backend server..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
