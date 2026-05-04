import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from indexer.db import get_connection, init_db
from Registry import Registry

def parse_registry_hive(filepath, hive_name=None):
    """
    Reads a Registry hive file and extracts forensically relevant keys.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    filename = os.path.basename(filepath)
    hive_label = hive_name or filename
    records_inserted = 0

    print(f"[REGISTRY] Reading hive: {filename}")

    try:
        reg = Registry.Registry(filepath)
    except Exception as e:
        print(f"[REGISTRY] Error opening hive: {e}")
        conn.close()
        return 0

    def walk_key(key, path=""):
        """Recursively walk all keys and store values."""
        nonlocal records_inserted
        current_path = f"{path}\\{key.name()}" if path else key.name()

        try:
            for value in key.values():
                try:
                    value_name = value.name() or "(Default)"
                    value_data = str(value.value()) or ""
                    value_type = str(value.value_type_str())

                    cursor.execute("""
                        INSERT INTO registry_entries
                        (hive, key_path, value_name, value_data, value_type, file_source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (hive_label, current_path, value_name, value_data, value_type, filename))

                    records_inserted += 1
                except Exception:
                    pass
        except Exception:
            pass

        try:
            for subkey in key.subkeys():
                walk_key(subkey, current_path)
        except Exception:
            pass

    walk_key(reg.root())

    conn.commit()
    conn.close()

    print(f"[REGISTRY] Done.")
    print(f"[REGISTRY] Records inserted: {records_inserted}")
    return records_inserted


def extract_forensic_artifacts(filepath, hive_name=None):
    """
    Extracts specific high-value forensic keys from a hive.
    Prints a summary of what was found.
    """
    hive_label = hive_name or os.path.basename(filepath)

    print(f"\n[FORENSIC ARTIFACTS] Scanning: {hive_label}")

    try:
        reg = Registry.Registry(filepath)
    except Exception as e:
        print(f"[REGISTRY] Error opening hive: {e}")
        return

    # Define forensic keys to look for
    forensic_keys = {
        "Installed Programs": [
            "Microsoft\\Windows\\CurrentVersion\\Uninstall",
        ],
        "Run at Startup": [
            "Microsoft\\Windows\\CurrentVersion\\Run",
            "Microsoft\\Windows\\CurrentVersion\\RunOnce",
        ],
        "Recent Documents": [
            "Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs",
        ],
        "Typed URLs (Browser)": [
            "Microsoft\\Internet Explorer\\TypedURLs",
        ],
        "Last Logged In User": [
            "Microsoft\\Windows\\CurrentVersion\\Authentication\\LogonUI",
        ],
        "Timezone": [
            "SYSTEM\\CurrentControlSet\\Control\\TimeZoneInformation",
            "ControlSet001\\Control\\TimeZoneInformation",
        ],
        "USB Devices": [
            "SYSTEM\\CurrentControlSet\\Enum\\USBSTOR",
            "CurrentControlSet\\Enum\\USBSTOR",
        ],
        "Network Interfaces": [
            "SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces",
            "CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces",
        ],
    }

    found_anything = False

    for artifact_name, key_paths in forensic_keys.items():
        for key_path in key_paths:
            try:
                key = reg.open(key_path)
                print(f"\n  [{artifact_name}] Found at: {key_path}")
                found_anything = True

                # Print subkeys (e.g. each installed program)
                try:
                    subkeys = list(key.subkeys())
                    if subkeys:
                        for sk in subkeys[:10]:  # limit to 10
                            print(f"    → {sk.name()}")
                        if len(subkeys) > 10:
                            print(f"    ... and {len(subkeys) - 10} more")
                except Exception:
                    pass

                # Print values
                try:
                    values = list(key.values())
                    if values:
                        for v in values[:5]:  # limit to 5
                            print(f"    {v.name()}: {str(v.value())[:80]}")
                except Exception:
                    pass

                break  # found this artifact, move to next

            except Exception:
                continue

    if not found_anything:
        print("  No forensic artifacts found in this hive.")
        print("  (This is normal — not all hives contain all key types)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parser/registry_parser.py <path_to_hive>")
        print("\nExample hive locations on a live system:")
        print("  SYSTEM   : C:\\Windows\\System32\\config\\SYSTEM")
        print("  SOFTWARE : C:\\Windows\\System32\\config\\SOFTWARE")
        print("  NTUSER   : C:\\Users\\<username>\\NTUSER.DAT")
    else:
        filepath = sys.argv[1]
        if not os.path.exists(filepath):
            print(f"[ERROR] File not found: {filepath}")
        else:
            extract_forensic_artifacts(filepath)
            parse_registry_hive(filepath)