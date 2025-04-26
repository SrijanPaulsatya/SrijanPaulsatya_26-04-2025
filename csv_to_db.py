import os
import csv
import sqlite3

def csv_data(path):
    with open(path, newline = '') as f:
        reader = csv.reader(f)
        next(reader)
        data = list(reader)

        return data

def create_db():
    if os.path.exists("stores.db"):
        return

    conn = sqlite3.connect("stores.db")
    cur = conn.cursor()


    cur.execute('DROP TABLE IF EXISTS store_status')
    cur.execute('DROP TABLE IF EXISTS menu_hours')
    cur.execute('DROP TABLE IF EXISTS timezones')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS store_status (
            store_id VARCHAR(255),
            status VARCHAR(10),
            timestamp_utc TIMESTAMP,
            FOREIGN KEY (store_id) REFERENCES timezones(store_id)
        )
    ''')

    cur.execute("CREATE INDEX IF NOT EXISTS idx_store_id ON store_status (store_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_timestamp_utc ON store_status (timestamp_utc)")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS menu_hours (
            store_id VARCHAR(255),
            dayOfWeek INT,
            start_time_local TIME DEFAULT '00:00:00',
            end_time_local TIME DEFAULT '24:00:00',
            FOREIGN KEY (store_id) REFERENCES timezones(store_id)
        )
    ''')

    cur.execute("CREATE INDEX IF NOT EXISTS idx_store_day ON menu_hours (store_id, dayOfWeek)")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS timezones (
            store_id VARCHAR(255) PRIMARY KEY,
            timezone_str VARCHAR(255) DEFAULT 'America/Chicago'
        )
    ''')


    status_data = csv_data("./data/store_status.csv")
    menu_hours_data = csv_data("./data/menu_hours.csv")
    timezones_data = csv_data("./data/timezones.csv")

    cur.executemany('INSERT INTO store_status VALUES (?,?,?)', status_data)
    cur.executemany('INSERT INTO menu_hours VALUES (?,?,?,?)', menu_hours_data)
    cur.executemany('INSERT INTO timezones VALUES (?,?)', timezones_data)


    conn.commit()
    conn.close()
