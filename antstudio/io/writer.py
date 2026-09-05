"""Universal output writer."""
import os, json, csv
from pathlib import Path
from typing import List, Dict, Any

class Results:
    def __init__(self, rows: List[Dict[str, Any]], quality: dict = None, audit: dict = None):
        self.rows = rows
        self.quality = quality or {}
        self.audit = audit or {}
        self.count = len(rows)

    @property
    def flagged(self):
        return Results([r for r in self.rows if r.get("_confidence", 1) < r.get("_threshold", 0.7)], self.quality, self.audit)

    @property
    def passed(self):
        return Results([r for r in self.rows if r.get("_confidence", 1) >= r.get("_threshold", 0.7)], self.quality, self.audit)

    def _clean(self):
        return [{k: v for k, v in r.items() if not k.startswith("_")} for r in self.rows]

    def to_csv(self, path: str):
        if not self.rows: return
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        keys = [k for k in self.rows[0] if not k.startswith("_")]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(self.rows)

    def to_excel(self, path: str):
        try:
            import openpyxl
            wb = openpyxl.Workbook(); ws = wb.active
            if not self.rows: wb.save(path); return
            keys = [k for k in self.rows[0] if not k.startswith("_")]
            ws.append(keys)
            for r in self.rows:
                ws.append([r.get(k, "") for k in keys])
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            wb.save(path)
        except ImportError:
            print("  pip install openpyxl")

    def to_json(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._clean(), f, indent=2, ensure_ascii=False)

    def to_database(self, conn: str, table: str = "results", mode: str = "append"):
        try:
            import sqlalchemy, pandas as pd
            engine = sqlalchemy.create_engine(conn)
            pd.DataFrame(self._clean()).to_sql(table, engine, if_exists=mode, index=False)
            print(f"  Saved {self.count} rows to {table}")
        except Exception as e:
            print(f"  DB write error: {e}")

    def to_webhook(self, url: str, method: str = "POST"):
        try:
            import httpx
            httpx.request(method, url, json={"results": self._clean()}, timeout=30)
        except Exception as e:
            print(f"  Webhook error: {e}")

    def save(self, path: str):
        ext = Path(path).suffix.lower()
        if ext == ".xlsx": self.to_excel(path)
        elif ext == ".json": self.to_json(path)
        else: self.to_csv(path)

    def __repr__(self):
        return f"Results({self.count} rows)"
    def __len__(self):
        return self.count
