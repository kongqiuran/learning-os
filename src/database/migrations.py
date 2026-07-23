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
    ("20260720_payment_orders", {}),
    ("20260720_ai_tasks", {
        "learning_packages": {
            "task_id": "INTEGER REFERENCES tasks(id) ON DELETE SET NULL",
        },
    }),
    ("20260723_document_pages", {}),
    ("20260723_visual_assets", {}),
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
            if version == "20260720_payment_orders":
                from src.models.payment_order import PaymentOrder

                PaymentOrder.__table__.create(bind=connection, checkfirst=True)
            if version == "20260720_ai_tasks":
                from src.models.task import Task

                Task.__table__.create(bind=connection, checkfirst=True)
            if version == "20260723_document_pages":
                from src.models.document_page import DocumentPage

                DocumentPage.__table__.create(bind=connection, checkfirst=True)
            if version == "20260723_visual_assets":
                from src.models.visual_asset import VisualAsset

                VisualAsset.__table__.create(bind=connection, checkfirst=True)
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
            if version == "20260720_ai_tasks":
                connection.execute(text("""
                    INSERT INTO tasks (
                        user_id, course_id, task_type, status, progress,
                        current_stage, resource_type, resource_id,
                        error_code, error_detail, created_at, updated_at,
                        started_at, finished_at
                    )
                    SELECT
                        courses.user_id,
                        learning_packages.course_id,
                        CASE
                            WHEN learning_packages.scene = 'legacy' THEN 'course_generation'
                            ELSE learning_packages.scene || '_generation'
                        END,
                        CASE learning_packages.status
                            WHEN 'pending' THEN 'PENDING'
                            WHEN 'processing' THEN 'RUNNING'
                            WHEN 'completed' THEN 'SUCCESS'
                            ELSE 'FAILED'
                        END,
                        CASE WHEN learning_packages.status = 'completed' THEN 100 ELSE 0 END,
                        COALESCE(learning_packages.current_stage, learning_packages.status),
                        'learning_package',
                        learning_packages.id,
                        learning_packages.error_type,
                        learning_packages.error_detail,
                        learning_packages.created_at,
                        CURRENT_TIMESTAMP,
                        learning_packages.claimed_at,
                        learning_packages.finished_at
                    FROM learning_packages
                    JOIN courses ON courses.id = learning_packages.course_id
                    WHERE learning_packages.task_id IS NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM tasks
                          WHERE tasks.resource_type = 'learning_package'
                            AND tasks.resource_id = learning_packages.id
                      )
                """))
                connection.execute(text("""
                    UPDATE learning_packages
                    SET task_id = (
                        SELECT tasks.id FROM tasks
                        WHERE tasks.resource_type = 'learning_package'
                          AND tasks.resource_id = learning_packages.id
                    )
                    WHERE task_id IS NULL
                """))
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_learning_packages_task_id ON learning_packages(task_id)"))
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (:version)"), {"version": version})
