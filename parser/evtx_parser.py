import sys
import os
import xml.etree.ElementTree as ET
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from indexer.db import get_connection, init_db

import Evtx.Evtx as evtx

NAMESPACE = "{http://schemas.microsoft.com/win/2004/08/events/event}"

def parse_evtx_file(filepath):
    """
    Reads a .evtx file and stores all records into the events table.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    filename = os.path.basename(filepath)
    records_inserted = 0
    records_failed = 0

    print(f"[PARSER] Reading: {filename}")

    try:
        with evtx.Evtx(filepath) as log:
            for record in log.records():
                try:
                    xml_str = record.xml()
                    root = ET.fromstring(xml_str)

                    # Extract System fields
                    system = root.find(f"{NAMESPACE}System")

                    event_id = ""
                    timestamp = ""
                    source = ""
                    computer = ""
                    level = ""

                    if system is not None:
                        eid = system.find(f"{NAMESPACE}EventID")
                        if eid is not None:
                            event_id = eid.text or ""

                        time_el = system.find(f"{NAMESPACE}TimeCreated")
                        if time_el is not None:
                            timestamp = time_el.attrib.get("SystemTime", "")

                        provider = system.find(f"{NAMESPACE}Provider")
                        if provider is not None:
                            source = provider.attrib.get("Name", "")

                        comp = system.find(f"{NAMESPACE}Computer")
                        if comp is not None:
                            computer = comp.text or ""

                        lvl = system.find(f"{NAMESPACE}Level")
                        if lvl is not None:
                            level_map = {
                                "1": "Critical",
                                "2": "Error",
                                "3": "Warning",
                                "4": "Information",
                                "5": "Verbose"
                            }
                            level = level_map.get(lvl.text, lvl.text or "")

                    # Extract EventData message
                    message_parts = []
                    event_data = root.find(f"{NAMESPACE}EventData")
                    if event_data is not None:
                        for data in event_data:
                            name = data.attrib.get("Name", "")
                            value = data.text or ""
                            if name:
                                message_parts.append(f"{name}: {value}")
                            elif value:
                                message_parts.append(value)

                    message = " | ".join(message_parts)

                    cursor.execute("""
                        INSERT INTO events 
                        (event_id, timestamp, source, computer, message, level, file_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (event_id, timestamp, source, computer, message, level, filename))

                    records_inserted += 1

                except Exception as e:
                    records_failed += 1
                    continue

    except Exception as e:
        print(f"[PARSER] Error opening file: {e}")
        conn.close()
        return

    conn.commit()
    conn.close()

    print(f"[PARSER] Done.")
    print(f"[PARSER] Records inserted : {records_inserted}")
    print(f"[PARSER] Records failed   : {records_failed}")
    return records_inserted


def get_event_summary():
    """
    Returns a summary of all events in the database.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM events")
    total = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT event_id, COUNT(*) as count 
        FROM events 
        GROUP BY event_id 
        ORDER BY count DESC 
        LIMIT 10
    """)
    top_events = cursor.fetchall()

    cursor.execute("SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest FROM events")
    time_range = cursor.fetchone()

    conn.close()
    return {
        "total": total,
        "top_events": [dict(r) for r in top_events],
        "earliest": time_range["earliest"],
        "latest": time_range["latest"]
    }


if __name__ == "__main__":
    # Test with a sample file
    if len(sys.argv) < 2:
        print("Usage: python parser/evtx_parser.py <path_to_evtx_file>")
        print("\nExample: python parser/evtx_parser.py tests/Security.evtx")
    else:
        filepath = sys.argv[1]
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
        else:
            parse_evtx_file(filepath)
            summary = get_event_summary()
            print(f"\n[SUMMARY]")
            print(f"  Total records : {summary['total']}")
            print(f"  Earliest event: {summary['earliest']}")
            print(f"  Latest event  : {summary['latest']}")
            print(f"  Top EventIDs  :")
            for e in summary['top_events']:
                print(f"    EventID {e['event_id']:>6} → {e['count']} records")