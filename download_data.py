"""Descarga los nueve CSV de Olist v2 sin modificar originales existentes."""
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import hashlib
import io
import json
import zipfile

BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "raw"
MANIFEST = BASE / "data" / "source_manifest.json"
URL = ("https://www.kaggle.com/api/v1/datasets/download/"
       "olistbr/brazilian-ecommerce?dataset_version_number=2")
FILES = [
    "olist_customers_dataset.csv", "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv", "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv", "olist_orders_dataset.csv",
    "olist_products_dataset.csv", "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    expected = {}
    if MANIFEST.exists():
        expected = {f["file"]: f["sha256"]
                    for f in json.loads(MANIFEST.read_text())["files"]}
    missing = [name for name in FILES if not (RAW / name).exists()]
    if missing:
        print("Descargando Olist v2 desde Kaggle...")
        request = Request(URL, headers={"User-Agent": "olist-course-project/1.0"})
        with urlopen(request, timeout=120) as response:
            content = response.read()
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            payload = {name: archive.read(name) for name in FILES}
        for name, data in payload.items():
            if name in expected and sha256(data) != expected[name]:
                raise ValueError(f"La fuente no coincide con el manifiesto: {name}")
        for name in missing:
            (RAW / name).write_bytes(payload[name])
    records = []
    for name in FILES:
        data = (RAW / name).read_bytes()
        digest = sha256(data)
        if name in expected and digest != expected[name]:
            raise ValueError(f"Original modificado: {name}. No se sobrescribió.")
        records.append({"file": name, "bytes": len(data), "sha256": digest})
    if not MANIFEST.exists():
        manifest = {
            "dataset": "olistbr/brazilian-ecommerce", "version": 2,
            "source_url": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
            "download_url": URL,
            "download_date": datetime.now(timezone.utc).date().isoformat(),
            "files": records,
        }
        MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Listo: nueve archivos verificados en {RAW}")


if __name__ == "__main__":
    main()
