import os
import csv
import sqlite3
import timeit
import pandas as pd
from reports import reports
from csv_to_db import create_db
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

create_db()

days = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

def local_time_converter(utc_time, timezone):
    dt_obj = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S.%f %Z")
    dt_obj = dt_obj.replace(tzinfo=ZoneInfo("UTC"))
    local_time = dt_obj.astimezone(ZoneInfo(timezone))
    return local_time.replace(microsecond=0)



def get_operational_hours(cur):
    store_hours = {}
    cur.execute('SELECT * FROM menu_hours')
    hours_data = cur.fetchall()

    #test for getting the time values and comparing them"
    for row in hours_data:
        store_id = row[0]
        dayOfWeek = days[row[1]]
        start_time = datetime.strptime(row[2], "%H:%M:%S").time()
        end_time = datetime.strptime(row[3], "%H:%M:%S").time()

        if store_id not in store_hours:
            store_hours[store_id] = {}
        if dayOfWeek not in store_hours[store_id]:
            store_hours[store_id][dayOfWeek] = []
        store_hours[store_id][dayOfWeek].append((start_time, end_time))

    return store_hours

#Function for checking if the time is between business hours
def business_hour_check(start_time, end_time, time):
    if start_time <= time <= end_time:
        return True
    else:
        return False

def generate_report(report_id):
    conn = sqlite3.connect("stores.db")
    cur = conn.cursor()

    cur.execute("SELECT timestamp_utc FROM store_status ORDER BY timestamp_utc DESC LIMIT 1")
    observation_time = local_time_converter(cur.fetchone()[0], "UTC")
    print(observation_time)


    cur.execute("SELECT store_id FROM timezones")
    stores = cur.fetchall()
    report = {}
    operational_hours = get_operational_hours(cur)


    for store in stores:
        store_id = store[0]

        activity_query = cur.execute("SELECT status, timestamp_utc, timezone_str FROM store_status JOIN timezones ON store_status.store_id = timezones.store_id WHERE timestamp_utc >= '2024-10-07 23:55:18.727055 UTC' AND timezones.store_id = ? ORDER BY timestamp_utc DESC ", (store_id,))
        activities = activity_query.fetchall()
        current_time = observation_time

        uptime_last_hour = 0
        uptime_last_day = 0
        uptime_last_week = 0
        downtime_last_hour = 0
        downtime_last_day = 0
        downtime_last_week = 0

        last_hour_last_status = None
        last_day_last_status = None
        last_week_last_status = None


        for activity in activities:
            store_status = activity[0]
            timestamp_utc = activity[1]
            logged_time_obj = local_time_converter(timestamp_utc, "UTC")
            timezone_str = activity[2]
            local_time = local_time_converter(timestamp_utc, timezone_str)
            timediff = current_time - logged_time_obj
            timediff_in_hours = timediff.total_seconds() / 3600

            print(f"Store_id: {store_id}")
            

            for time in operational_hours.get(store_id, {}).get(local_time.strftime("%A"), []):
                start_time = time[0]
                end_time = time[1]

                is_within_business_hours = business_hour_check(start_time, end_time, local_time.time())
                observation_diff = observation_time - logged_time_obj

                if is_within_business_hours:

                    if observation_diff <= timedelta(hours=1):
                        last_hour_last_status  = store_status
                        if store_status == 'active':
                            uptime_last_hour += timediff.seconds / 60
                        if store_status == 'inactive':
                            downtime_last_hour += timediff.seconds / 60

                    if observation_diff <= timedelta(days=1) :
                        last_day_last_status = store_status
                        if store_status == 'active':
                            uptime_last_day += timediff_in_hours
                        if store_status == "inactive":
                            downtime_last_day += timediff_in_hours

                    if observation_diff <= timedelta(days=7):
                        last_week_last_status = store_status
                        if store_status == "active":
                            uptime_last_week += timediff_in_hours
                        if store_status == "inactive":
                            downtime_last_week += timediff_in_hours

                else:
                    continue

            current_time = logged_time_obj

        total_last_hour = uptime_last_hour + downtime_last_hour
        total_last_day = uptime_last_day + downtime_last_day
        total_last_week = uptime_last_week + downtime_last_week

        if total_last_hour != 60 and total_last_hour <= 60:
            if last_hour_last_status == "active":
                uptime_last_hour += 60 - total_last_hour
            if last_hour_last_status == "inactive":
                downtime_last_hour += 60 - total_last_hour

        if total_last_day != 24:
            if last_day_last_status == "active":
                uptime_last_day += 24 - total_last_day
            if last_day_last_status == "inactive":
                downtime_last_day += 24 - total_last_day

        if total_last_week != 168:
            if last_week_last_status == "active":
                uptime_last_week += 168 - total_last_week
            if last_week_last_status == "inactive":
                downtime_last_week += 168 - total_last_week


        report[store_id] = {
            "uptime_last_hour(in minutes)": round(uptime_last_hour,2),
            "uptime_last_day(in hours)": round(uptime_last_day,2),
            "uptime_last_week(in hours)": round(uptime_last_week,2),
            "downtime_last_hour(in minutes)": round(downtime_last_hour,2),
            "downtime_last_day(in hours)": round(downtime_last_day,2),
            "downtime_last_week(in hours)": round(downtime_last_week,2)
        }
    
    os.makedirs("./reports", exist_ok=True)
    path = f"./reports/{report_id}.csv"

    df = pd.DataFrame.from_dict(report, orient="index")
    df.index.name = 'id'
    df.to_csv(path)
    reports[report_id]["status"] = "Complete"
    reports[report_id]["csv_path"] = path

    return 0
