import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# =========================================================================
# Config - Need admin with CRUD permissions on connector and solutionpacks
# =========================================================================
HOST     = "FSR_IP"
USERNAME = "admin"
PASSWORD = "password"

BASE_URL = f"https://{HOST}"
SESSION  = requests.Session()
SESSION.verify = False


# ===============
# Login
# ===============
def login():
    resp = SESSION.post(f"{BASE_URL}/auth/authenticate",
                        json={"credentials": {"loginid": USERNAME, "password": PASSWORD}}
    )
    resp.raise_for_status()
    token = resp.json().get("token")
    if not token:
        raise ValueError("Login failed: no token returned.")
    SESSION.headers.update({"Authorization": f"Bearer {token}"})
    print("\n[OK] Logged in successfully.")


# ======================
# List all connectors
# ======================
def list_connectors():
    url  = f"{BASE_URL}/api/query/solutionpacks"
    body = {
        "sort": [{"field": "label", "direction": "ASC"}],
        "page": 1,
        "limit": 100,
        "logic": "AND",
        "filters": [
            {"field": "type",      "operator": "in", "value": ["connector"]},
            {"field": "installed", "operator": "eq", "value": True},
            {
                "logic": "OR",
                "filters": [
                    {"field": "development", "operator": "eq", "value": False},
                    {"field": "type",        "operator": "eq", "value": "widget"},
                    {"field": "type",        "operator": "eq", "value": "solutionpack"}
                ]
            }
        ]
    }
    resp = SESSION.post(url, json=body)
    resp.raise_for_status()
    members = resp.json().get("hydra:member", [])
    return [
        {
            "label": c.get("label", ""),
            "name": c.get("name", ""),
            "version": c.get("version", ""),
            "status": c.get("status") or (c.get("solutionPack") or {}).get("status", "")
        }
        for c in members
    ]


# =========================================================================
# List installed connectors and prompt user to select a connector to export
# =========================================================================
def prompt_connector_selection(connectors):
    col_w = {"#": 4, "Label": 40, "Name": 35, "Version": 10, "Status": 12}
    header = (f"{'#':<{col_w['#']}}  {'Label':<{col_w['Label']}}  "
              f"{'Name':<{col_w['Name']}}  {'Version':<{col_w['Version']}}  "
              f"{'Status':<{col_w['Status']}}")
    print("\n" + "-" * len(header))
    print("  Installed Connectors")
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for i, c in enumerate(connectors, start=1):
        print(f"{i:<{col_w['#']}}  {c['label']:<{col_w['Label']}}  "
              f"{c['name']:<{col_w['Name']}}  {c['version']:<{col_w['Version']}}  "
              f"{c['status']:<{col_w['Status']}}")
    print("-" * len(header))

    name_map = {c["name"]: c for c in connectors}
    while True:
        choice = input("\nEnter connector name to export (from 'Name' column): ").strip()
        if choice in name_map:
            return name_map[choice]
        print(f"  [!] '{choice}' not found. Please enter the exact name from the list above.")

# ==================================================
# GET connector detalils and fetch 'connector_id'
# ==================================================
def get_connector_details(name, version):
    url  = f"{BASE_URL}/api/integration/connectors/{name}/{version}/"
    resp = SESSION.post(url, json={})
    resp.raise_for_status()
    connector_id = resp.json().get("id")
    if not connector_id:
        raise ValueError(f"Could not retrieve 'id' for connector '{name}' v{version}.")
    print(f"[/] Connector ID: {connector_id}")
    return connector_id

# =========================================
# EXPORT CONNECTOR and save as .tgz file
# =========================================
def export_connector(connector_id, name, version):
    url  = f"{BASE_URL}/api/integration/connector/development/entity/{connector_id}/export/"
    resp = SESSION.get(url, params={"format": "json"}, stream=True)
    resp.raise_for_status()

    cd = resp.headers.get("Content-Disposition", "")
    filename = cd.split("filename=")[-1].strip().strip('"') if "filename=" in cd else f"{name}-{version}.tgz"

    output_path = os.path.join(os.getcwd(), filename)
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"[OK] Connector exported -> {output_path}")
    return output_path

# ==================
# IMPORT CONNECTOR
# =================
def import_connector():
    print("\n---------- Import Connector -----------------------------")

    # Find all .tgz files in the current directory
    tgz_files = [f for f in os.listdir(os.getcwd()) if f.endswith(".tgz")]

    if not tgz_files:
        print("[!] No .tgz files found in current directory.")
        print(f"    Directory: {os.getcwd()}")
        return

    # Display available files
    print(f"\nAvailable .tgz files in: {os.getcwd()}\n")
    for i, f in enumerate(tgz_files, start=1):
        size = os.path.getsize(os.path.join(os.getcwd(), f))
        print(f"  {i}. {f}  ({size / 1024:.1f} KB)")

    # Prompt user to select
    while True:
        choice = input("\nSelect file number to import: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(tgz_files):
            tgz_path = os.path.join(os.getcwd(), tgz_files[int(choice) - 1])
            break
        print(f"  [!] Please enter a number between 1 and {len(tgz_files)}.")

    url = f"{BASE_URL}/api/3/solutionpacks/install"
    params = {"$type": "connector", "$replace": "true"}

    with open(tgz_path, "rb") as f:
        files = {"file": (os.path.basename(tgz_path), f, "application/octet-stream")}
        resp = SESSION.post(url, params=params, files=files)

    resp.raise_for_status()
    print(f"\n[/] Connector imported successfully: {os.path.basename(tgz_path)}")
    print(f"    Response: {resp.json()}")


# =======
# Logout
# =======
def logout():
    SESSION.post(f"{BASE_URL}/api/3/logout", json={})
    print("[OK] Logged out.")

# ===========
#  Main Menu
# ===========
def main():
    try:
        login()

        print("_______________________________")
        print("|   FortiSOAR Connector Tool  |")
        print("|-----------------------------|")
        print("|  1. Export Connector        |")
        print("|  2. Import Connector        |")
        print("|_____________________________|")

        while True:
            mode = input("\nSelect option (1/2): ").strip()
            if mode in ("1", "2"):
                break
            print("  [!] Please enter 1 or 2.")

        if mode == "1":
            connectors = list_connectors()
            if not connectors:
                print("[!] No installed connectors found.")
                return
            selected = prompt_connector_selection(connectors)
            print(f"\n[->] Selected: {selected['label']} ({selected['name']} v{selected['version']})")
            connector_id = get_connector_details(selected["name"], selected["version"])
            export_connector(connector_id, selected["name"], selected["version"])

        elif mode == "2":
            import_connector()

    except requests.HTTPError as e:
        print(f"\n[X] HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n[X] Error: {e}")

    logout()

if __name__ == "__main__":
    main()
