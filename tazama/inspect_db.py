import psycopg2
import os

try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="postgres",
        user="postgres",
        password=None 
    )
    cur = conn.cursor()
    
    # List tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print("Tables:", tables)
    
    # Cek isi salah satu tabel yang relevant (jika ada)
    # Biasanya ada 'classification_process' atau 'transactions'
    
    conn.close()
except Exception as e:
    print("Error:", e)
