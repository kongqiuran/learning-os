from sqlalchemy import inspect, text


MIGRATIONS = (
    ("20260719_v2", {
        "documents": {"chapter_id": "INTEGER REFERENCES chapters(id) ON DELETE SET NULL"},
        "learning_packages": {
            "scene": "VARCHAR(20) NOT NULL DEFAULT 'legacy'",
            "scope_document_id": "INTEGER REFERENCES documents(id) ON DELETE SET NULL",
            "usage_record_id": "INTEGER REFERENCES usage_records(id) ON DELETE SET NULL",
            "entitlement_id": "INTEGER REFERENCES course_entitlements(id) ON DELETE SET NULL",
            "heartbeat_at": "DATETIME",
            "claimed_at": "DATETIME",
            "finished_at": "DATETIME",
            "task_attempts": "INTEGER NOT NULL DEFAULT 0",
        },
    }),
    ("20260719_v2_entitlement", {
        "learning_packages": {"entitlement_id": "INTEGER REFERENCES course_entitlements(id) ON DELETE SET NULL"},
    }),
)


def run_schema_migrations(engine):
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(80) PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"))
        applied = {row[0] for row in connection.execute(text("SELECT version FROM schema_migrations"))}
        for version, tables in MIGRATIONS:
            if version in applied:
                continue
            inspector = inspect(connection)
            for table_name, columns in tables.items():
                existing = {column["name"] for column in inspector.get_columns(table_name)}
                for name, definition in columns.items():
                    if name not in existing:
                        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {definition}"))
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (:version)"), {"version": version})
