# FortiSOAR Connector Export/Import Tool

A Python CLI tool to **export** installed FortiSOAR connectors to a `.tgz` and **import** a connector `.tgz` into FortiSOAR.


---

## Features

- Export an installed connector to a `.tgz`
- Import a connector `.tgz` (replace existing)
- No interactive prompts (safe for automation)

---

## Requirements

- Python 3.8+
- `requests`

Install:

```bash
pip install requests
```

---

## Configuration

Set these environment variables:

- `FSR_HOST` – FortiSOAR IP/DNS
- `FSR_USERNAME` – username
- `FSR_PASSWORD` – password

Use a admin user with CRUD permissions on Connector and SolutionPacks modules.

---

## Usage

### Export a connector

Example (export a specific connector name/version):

```bash
python export_import_connector.py export --name "<connector_name>" --version "<connector_version>"
```

### Import a connector

```bash
python export_import_connector.py import --file "./MyConnector-1.0.0.tgz"
```

> The script will show already present files in the current directory
---

## TLS / Certificates

The script may use `verify=False` for lab environments. In production, prefer TLS verification and point Requests to your CA bundle (Requests supports passing `verify` a CA bundle path).

---

## Troubleshooting

### Missing env vars

If the script exits with an error like “FSR_HOST not set”, confirm the variables are set in the same shell/session where you run the script. Environment variables are process-scoped.

### `requests` not found

Install into the interpreter you are using:

```bash
python -m pip install requests
```
