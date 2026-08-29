"""Save to Database Node — write results to SQL/NoSQL databases."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class SaveToDatabaseNode(BaseNode):
    node_type = "save_to_database"
    label = "Save to Database"
    category = "output"
    description = "Save results to SQLite, PostgreSQL, MySQL, or MongoDB"
    color = "#059669"

    def define_inputs(self):
        return [Port("data", PortType.ANY, "Data to save")]

    def define_outputs(self):
        return [
            Port("status", PortType.TEXT, "Save status"),
            Port("rows_saved", PortType.FLOAT, "Number of rows saved"),
        ]

    def define_config(self):
        return [
            NodeConfig("db_type", "Database Type", "select", default="sqlite",
                       options=["sqlite", "postgresql", "mysql", "mongodb"]),
            NodeConfig("connection_string", "Connection String", "string",
                       default="sqlite:///output/results.db"),
            NodeConfig("table", "Table / Collection Name", "string", default="results"),
            NodeConfig("mode", "Write Mode", "select", default="append", options=["append", "replace"]),
        ]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        db_type = config.get("db_type", "sqlite")
        table = config.get("table", "results")
        mode = config.get("mode", "append")

        if isinstance(data, dict):
            rows = [data]
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            rows = data
        else:
            rows = [{"result": str(data)}]

        try:
            if db_type == "sqlite":
                import sqlite3, os, json
                db_path = config.get("connection_string", "").replace("sqlite:///", "")
                os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
                conn = sqlite3.connect(db_path)
                cols = list(rows[0].keys())
                col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
                conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')
                if mode == "replace":
                    conn.execute(f'DELETE FROM "{table}"')
                placeholders = ", ".join("?" for _ in cols)
                for row in rows:
                    vals = [json.dumps(row[c]) if isinstance(row[c], (dict, list)) else str(row.get(c, "")) for c in cols]
                    conn.execute(f'INSERT INTO "{table}" ({", ".join(f"{c}" for c in cols)}) VALUES ({placeholders})', vals)
                conn.commit(); conn.close()

            elif db_type in ("postgresql", "mysql"):
                import sqlalchemy, json
                engine = sqlalchemy.create_engine(config.get("connection_string", ""))
                import pandas as pd
                df = pd.DataFrame(rows)
                if_exists = "replace" if mode == "replace" else "append"
                df.to_sql(table, engine, if_exists=if_exists, index=False)

            elif db_type == "mongodb":
                from pymongo import MongoClient
                conn_str = config.get("connection_string", "mongodb://localhost:27017")
                client = MongoClient(conn_str)
                db_name = config.get("connection_string", "").split("/")[-1] or "antstudio"
                db = client[db_name]
                if mode == "replace":
                    db[table].drop()
                db[table].insert_many(rows)
                client.close()

            return NodeResult(
                outputs={"status": f"Saved to {db_type}/{table}", "rows_saved": len(rows)},
                message=f"Saved {len(rows)} rows to {db_type}:{table}",
            )
        except ImportError as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Missing dependency: {e}")
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Save failed: {e}")
