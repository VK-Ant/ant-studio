"""Database Input Node — connect to SQL/NoSQL databases."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class DatabaseInputNode(BaseNode):
    node_type = "database_input"
    label = "Database Input"
    category = "input"
    description = "Connect to SQLite, PostgreSQL, MySQL, or MongoDB"
    color = "#6366f1"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [
            Port("data", PortType.DICT, "Query results as dict"),
            Port("rows", PortType.LIST, "List of row dicts"),
            Port("row_count", PortType.FLOAT, "Number of rows returned"),
            Port("columns", PortType.LIST, "Column names"),
        ]

    def define_config(self):
        return [
            NodeConfig("db_type", "Database Type", "select", default="sqlite",
                       options=["sqlite", "postgresql", "mysql", "mongodb"]),
            NodeConfig("connection_string", "Connection String", "string",
                       default="sqlite:///data/mydb.sqlite"),
            NodeConfig("query", "SQL Query / Collection", "text_area",
                       default="SELECT * FROM documents LIMIT 100"),
            NodeConfig("host", "Host (if not in connection string)", "string", default="localhost"),
            NodeConfig("port", "Port", "number", default=5432),
            NodeConfig("database", "Database Name", "string", default=""),
            NodeConfig("username", "Username", "string", default=""),
            NodeConfig("password", "Password", "string", default=""),
        ]

    async def execute(self, inputs, config, context):
        db_type = config.get("db_type", "sqlite")
        conn_str = config.get("connection_string", "")
        query = config.get("query", "")

        try:
            if db_type == "sqlite":
                import sqlite3
                db_path = conn_str.replace("sqlite:///", "")
                if not os.path.isfile(db_path):
                    return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"SQLite DB not found: {db_path}")
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query)
                rows = [dict(row) for row in cursor.fetchall()]
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                conn.close()

            elif db_type in ("postgresql", "mysql"):
                try:
                    import sqlalchemy
                    engine = sqlalchemy.create_engine(conn_str)
                    with engine.connect() as conn:
                        result = conn.execute(sqlalchemy.text(query))
                        columns = list(result.keys())
                        rows = [dict(zip(columns, row)) for row in result.fetchall()]
                except ImportError:
                    return NodeResult(outputs={}, status=NodeStatus.ERROR,
                                      message="pip install sqlalchemy psycopg2-binary (PostgreSQL) or pymysql (MySQL)")

            elif db_type == "mongodb":
                try:
                    from pymongo import MongoClient
                    host = config.get("host", "localhost")
                    port = int(config.get("port", 27017))
                    db_name = config.get("database", "")
                    client = MongoClient(host, port)
                    db = client[db_name]
                    collection_name = query.strip()
                    rows = list(db[collection_name].find({}, {"_id": 0}).limit(1000))
                    columns = list(rows[0].keys()) if rows else []
                    client.close()
                except ImportError:
                    return NodeResult(outputs={}, status=NodeStatus.ERROR, message="pip install pymongo")
            else:
                return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Unsupported DB: {db_type}")

            data = {col: [row.get(col) for row in rows] for col in columns} if columns else {}
            return NodeResult(
                outputs={"data": data, "rows": rows, "row_count": len(rows), "columns": columns},
                message=f"Fetched {len(rows)} rows from {db_type}",
            )
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Database error: {e}")
