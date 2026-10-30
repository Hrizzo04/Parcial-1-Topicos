"""Configuración del agente y conexión a Supabase."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configuración cargada desde variables de entorno."""

    database_url: str
    database_schema: str = "public"
    sql_echo: bool = False


def _database_url_from_parts() -> str:
    host = os.getenv("SUPABASE_DB_HOST")
    user = os.getenv("SUPABASE_DB_USER")
    password = os.getenv("SUPABASE_DB_PASSWORD")

    if not all((host, user, password)):
        raise ValueError(
            "Configura SUPABASE_DATABASE_URL o las variables "
            "SUPABASE_DB_HOST, SUPABASE_DB_USER y SUPABASE_DB_PASSWORD."
        )

    port = os.getenv("SUPABASE_DB_PORT", "5432")
    name = os.getenv("SUPABASE_DB_NAME", "postgres")
    encoded_user = quote_plus(user or "")
    encoded_password = quote_plus(password or "")
    return (
        f"postgresql+psycopg2://{encoded_user}:{encoded_password}@"
        f"{host}:{port}/{name}?sslmode=require"
    )


@lru_cache()
def get_settings() -> Settings:
    """Lee la configuración sin exponer credenciales en mensajes de error."""
    database_url = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        database_url = _database_url_from_parts()
    
    # Normalización del driver para SQLAlchemy usando psycopg2
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg2://" + database_url.removeprefix("postgres://")
    elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+psycopg2://"):
        database_url = "postgresql+psycopg2://" + database_url.removeprefix("postgresql://")

    return Settings(
        database_url=database_url,
        database_schema=os.getenv("SUPABASE_DB_SCHEMA", "public"),
        sql_echo=os.getenv("SQL_ECHO", "false").strip().lower() in {"1", "true", "yes"},
    )