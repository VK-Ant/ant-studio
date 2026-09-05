"""Universal input reader."""
import os
from pathlib import Path
from typing import List, Tuple

def read_input(source: str = "", db: str = "", query: str = "",
               azure: str = "", s3: str = "", container: str = "",
               path: str = "", url: str = "", extensions: str = ".pdf,.docx,.txt,.csv",
               recursive: bool = True, max_files: int = 0) -> List[Tuple[str, bytes, str]]:
    results = []
    exts = [e.strip().lower() for e in extensions.split(",") if e.strip()]

    if source and os.path.isfile(source):
        with open(source, "rb") as f:
            return [(os.path.basename(source), f.read(), os.path.abspath(source))]

    if source and os.path.isdir(source):
        files = []
        if recursive:
            for root, _, fns in os.walk(source):
                for fn in fns:
                    if any(fn.lower().endswith(e) for e in exts):
                        files.append(os.path.join(root, fn))
        else:
            files = [os.path.join(source, fn) for fn in os.listdir(source)
                     if os.path.isfile(os.path.join(source, fn)) and any(fn.lower().endswith(e) for e in exts)]
        if max_files > 0:
            files = files[:max_files]
        for fp in files:
            try:
                with open(fp, "rb") as f:
                    results.append((os.path.basename(fp), f.read(), os.path.abspath(fp)))
            except Exception:
                pass
        return results

    if db:
        try:
            import sqlalchemy, pandas as pd
            engine = sqlalchemy.create_engine(db)
            df = pd.read_sql(query or "SELECT * FROM documents", engine)
            import json
            data = json.dumps(df.to_dict("records")).encode()
            return [("db_query.json", data, db)]
        except Exception as e:
            print(f"  DB error: {e}")

    if url:
        try:
            import httpx
            resp = httpx.get(url, follow_redirects=True, timeout=30)
            return [(url.split("/")[-1] or "download", resp.content, url)]
        except Exception as e:
            print(f"  URL error: {e}")

    return results
