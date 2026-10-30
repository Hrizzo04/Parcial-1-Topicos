"""Conexión y gestión de sesiones para la BDOO (Trazabilidad y memoria del agente)."""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_bdoo import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Error: Configura DATABASE_URL o SUPABASE_DATABASE_URL en tu archivo .env")

# Normalizar el driver para usar psycopg2
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL.removeprefix("postgres://")
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL.removeprefix("postgresql://")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def inicializar_bdoo():
    """Crea automáticamente las tablas bdoo_* en Supabase si no existen."""
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas BDOO inicializadas correctamente en Supabase.")


def get_db():
    """Provee una sesión limpia de BDOO para cada interacción."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()