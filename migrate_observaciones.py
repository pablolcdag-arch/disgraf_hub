import sqlite3
import os

def main():
    data_dir = os.environ.get("DATA_DIR", "./data")
    db_path = os.path.join(data_dir, "disgraf_hub.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE comprobantes ADD COLUMN observaciones TEXT DEFAULT NULL")
        print("Column 'observaciones' added successfully.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
