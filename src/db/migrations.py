"""Small additive migrations for existing CyberSRS SQLite databases."""

from __future__ import annotations

from sqlalchemy import Engine, inspect

_ADDITIVE_COLUMNS: dict[str, dict[str, str]] = {
    "project_context": {"model_run_id": "VARCHAR(36)"},
    "clarification_question": {"model_run_id": "VARCHAR(36)"},
    "srs_version": {
        "model_variant": "VARCHAR(20)",
        "model_name": "VARCHAR(100)",
        "adapter_name": "VARCHAR(100)",
        "rag_enabled": "BOOLEAN",
        "generation_metadata": "JSON",
        "model_run_id": "VARCHAR(36)",
    },
    "phase5_evaluation_run": {"model_run_id": "VARCHAR(36)"},
}

_MODEL_RUN_INDEXES: dict[str, str] = {
    table_name: f"ix_{table_name}_model_run_id" for table_name in _ADDITIVE_COLUMNS
}


def apply_compatibility_migrations(engine: Engine) -> None:
    """Add nullable provenance links without rewriting existing artifact rows.

    ``Base.metadata.create_all`` creates the new ``model_run`` table first.
    SQLite cannot add a foreign-key constraint to an existing table in place,
    so migrated databases receive nullable indexed link columns; fresh
    databases receive the full ORM-declared foreign keys. Application-level
    writes only associate IDs created in ``model_run``.
    """
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table_name, additions in _ADDITIVE_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in additions.items():
                if column_name not in columns:
                    connection.exec_driver_sql(
                        f'ALTER TABLE "{table_name}" '
                        f'ADD COLUMN "{column_name}" {column_type}'
                    )
            if "model_run_id" in additions:
                index_name = _MODEL_RUN_INDEXES[table_name]
                connection.exec_driver_sql(
                    f'CREATE INDEX IF NOT EXISTS "{index_name}" '
                    f'ON "{table_name}" (model_run_id)'
                )
