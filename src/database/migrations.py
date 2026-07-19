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
    ("20260719_chapter_scoped_packages", {
        "learning_packages": {
            "scope_chapter_id": "INTEGER REFERENCES chapters(id) ON DELETE SET NULL",
            "scope_unassigned": "BOOLEAN NOT NULL DEFAULT 0",
        },
    }),
    ("20260719_generation_scope_metadata", {
        "learning_packages": {
            "scope_kind": "VARCHAR(20) NOT NULL DEFAULT 'course'",
            "scope_key": "VARCHAR(80) NOT NULL DEFAULT 'course'",
            "source_fingerprint": "VARCHAR(64)",
            "prompt_version": "VARCHAR(40)",
        },
    }),
    ("20260719_quota_settlement", {
        "learning_packages": {
            "quota_source": "VARCHAR(30)",
            "quota_state": "VARCHAR(20)",
            "quota_units": "INTEGER NOT NULL DEFAULT 1",
            "quota_reserved_at": "DATETIME",
            "quota_settled_at": "DATETIME",
        },
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
            if version == "20260719_generation_scope_metadata":
                connection.execute(text("UPDATE learning_packages SET scope_kind = 'document', scope_key = 'document:' || scope_document_id WHERE scope_document_id IS NOT NULL"))
                connection.execute(text("UPDATE learning_packages SET scope_kind = 'chapter', scope_key = 'chapter:' || scope_chapter_id WHERE scope_chapter_id IS NOT NULL"))
                connection.execute(text("UPDATE learning_packages SET scope_kind = 'unassigned', scope_key = 'unassigned' WHERE scope_unassigned = 1"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS ix_learning_packages_scope_lookup ON learning_packages(course_id, scene, scope_key, version DESC)"))
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (:version)"), {"version": version})
