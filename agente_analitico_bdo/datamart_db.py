"""Conexión y operaciones de lectura controladas para el Data Mart en Supabase."""

from __future__ import annotations

from typing import Any
from sqlalchemy import Engine, create_engine, inspect, text
from config import Settings, get_settings


class DataMartDatabase:
    """Acceso de solo lectura al Data Mart mediante SQLAlchemy."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.engine: Engine = create_engine(
            self.settings.database_url,
            echo=self.settings.sql_echo,
            pool_pre_ping=True,
        )
        self.schema = self.settings.database_schema or "public"

    def test_connection(self) -> None:
        """Lanza un error explícito si no es posible conectar con la base de datos."""
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def list_tables(self) -> list[str]:
        """Devuelve las tablas y vistas visibles del esquema configurado."""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names(schema=self.schema)
        views = inspector.get_view_names(schema=self.schema)
        return sorted(set(tables + views))

    def list_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Devuelve nombre y tipo de las columnas de una tabla existente."""
        self._validate_table(table_name)
        columns = inspect(self.engine).get_columns(
            table_name, schema=self.schema
        )
        return [
            {"columna": column["name"], "tipo": str(column["type"])}
            for column in columns
        ]

    def preview_table(self, table_name: str, limit: int = 5) -> list[dict[str, Any]]:
        """Muestra un número acotado de filas de una tabla conocida."""
        self._validate_table(table_name)
        if not 1 <= limit <= 100:
            raise ValueError("El límite de filas debe estar entre 1 y 100.")

        preparer = self.engine.dialect.identifier_preparer
        schema_quoted = preparer.quote_schema(self.schema)
        table_quoted = preparer.quote(table_name)
        statement = text(f"SELECT * FROM {schema_quoted}.{table_quoted} LIMIT :row_limit")
        
        with self.engine.connect() as connection:
            rows = connection.execute(statement, {"row_limit": limit}).mappings()
            return [dict(row) for row in rows]

    def execute_read_query(
        self, statement: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Ejecuta una consulta de lectura del catálogo predefinido con control de seguridad."""
        clean_statement = statement.strip().upper()
        if not (clean_statement.startswith("SELECT") or clean_statement.startswith("WITH")):
            raise ValueError(
                "Operación no autorizada: El Data Mart solo admite consultas de lectura (SELECT / WITH)."
            )

        with self.engine.connect() as connection:
            result = connection.execute(text(statement), parameters or {})
            return [dict(row) for row in result.mappings()]

    def _validate_table(self, table_name: str) -> None:
        """Verifica la existencia de la tabla para evitar Inyecciones SQL por nombre de tabla."""
        if table_name not in self.list_tables():
            raise ValueError(
                f"La tabla '{table_name}' no existe en el esquema '{self.schema}'."
            )

    def close(self) -> None:
        """Libera el pool de conexiones del motor."""
        self.engine.dispose()


Database = DataMartDatabase