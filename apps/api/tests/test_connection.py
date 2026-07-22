import sys
from sqlalchemy import text
from core.db import engine

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Conexão OK:", result.scalar())
except Exception as e:
    print("Falha na conexão:", e)