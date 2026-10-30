"""Entidades ORM y objetos de intercambio del componente BDOO."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Session, declarative_base, relationship

Base = declarative_base()


class Usuario(Base):
    """Representa a quien formula la pregunta gerencial."""

    __tablename__ = "bdoo_usuario"

    usuario_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    rol = Column(String(50), nullable=False)

    sesiones = relationship("Sesion", back_populates="usuario")


class Sesion(Base):
    """Agrupa la conversación activa y su contexto temporal."""

    __tablename__ = "bdoo_sesion"

    sesion_id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(
        Integer, ForeignKey("bdoo_usuario.usuario_id"), nullable=False
    )
    fecha_inicio = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activa = Column(Boolean, default=True, nullable=False)

    usuario = relationship("Usuario", back_populates="sesiones")
    preguntas = relationship("Pregunta", back_populates="sesion")


class Pregunta(Base):
    """Conserva el texto original y la fecha de registro."""

    __tablename__ = "bdoo_pregunta"

    pregunta_id = Column(Integer, primary_key=True, autoincrement=True)
    sesion_id = Column(Integer, ForeignKey("bdoo_sesion.sesion_id"), nullable=False)
    texto_original = Column(Text, nullable=False)
    fecha_registro = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    sesion = relationship("Sesion", back_populates="preguntas")
    intencion = relationship("Intencion", uselist=False, back_populates="pregunta")


class Intencion(Base):
    """Representa la necesidad analítica extraída de una pregunta."""

    __tablename__ = "bdoo_intencion"

    intencion_id = Column(Integer, primary_key=True, autoincrement=True)
    pregunta_id = Column(
        Integer,
        ForeignKey("bdoo_pregunta.pregunta_id"),
        nullable=False,
        unique=True,
    )
    tipo_intencion = Column(String(100), nullable=False)
    metrica = Column(String(50))
    dimension = Column(String(50))
    periodo = Column(String(50))
    operacion = Column(String(50))

    pregunta = relationship("Pregunta", back_populates="intencion")
    consulta = relationship(
        "ConsultaAnalitica", uselist=False, back_populates="intencion"
    )


class ConsultaAnalitica(Base):
    """Almacena el SQL ejecutado y sus parámetros."""

    __tablename__ = "bdoo_consulta_analitica"

    consulta_id = Column(Integer, primary_key=True, autoincrement=True)
    intencion_id = Column(
        Integer,
        ForeignKey("bdoo_intencion.intencion_id"),
        nullable=False,
        unique=True,
    )
    sql_ejecutado = Column(Text, nullable=False)
    parametros_json = Column(Text)

    intencion = relationship("Intencion", back_populates="consulta")
    resultado = relationship(
        "ResultadoConsulta", uselist=False, back_populates="consulta"
    )


class ResultadoConsulta(Base):
    """Conserva los datos devueltos y metadatos de rendimiento."""

    __tablename__ = "bdoo_resultado_consulta"

    resultado_id = Column(Integer, primary_key=True, autoincrement=True)
    consulta_id = Column(
        Integer,
        ForeignKey("bdoo_consulta_analitica.consulta_id"),
        nullable=False,
        unique=True,
    )
    filas_devueltas = Column(Integer, nullable=False)
    datos_json = Column(Text, nullable=False)
    tiempo_ejecucion_ms = Column(Float, nullable=False)

    consulta = relationship("ConsultaAnalitica", back_populates="resultado")
    respuesta = relationship(
        "RespuestaAgente", uselist=False, back_populates="resultado"
    )


class RespuestaAgente(Base):
    """Almacena la explicación estructurada entregada al usuario."""

    __tablename__ = "bdoo_respuesta_agente"

    respuesta_id = Column(Integer, primary_key=True, autoincrement=True)
    resultado_id = Column(
        Integer,
        ForeignKey("bdoo_resultado_consulta.resultado_id"),
        nullable=False,
        unique=True,
    )
    texto_respuesta = Column(Text, nullable=False)
    interpretacion_gerencial = Column(Text, nullable=False)
    advertencias = Column(Text)
    fecha_respuesta = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    resultado = relationship("ResultadoConsulta", back_populates="respuesta")
    fuentes = relationship("FuenteDato", back_populates="respuesta")
    reglas = relationship("ReglaValidacion", back_populates="respuesta")


class FuenteDato(Base):
    """Identifica las tablas, dimensiones y campos consultados."""

    __tablename__ = "bdoo_fuente_dato"

    fuente_id = Column(Integer, primary_key=True, autoincrement=True)
    respuesta_id = Column(
        Integer, ForeignKey("bdoo_respuesta_agente.respuesta_id"), nullable=False
    )
    tabla_hechos = Column(String(50), nullable=False)
    dimensiones_utilizadas = Column(String(200), nullable=False)

    respuesta = relationship("RespuestaAgente", back_populates="fuentes")


class ReglaValidacion(Base):
    """Registra controles de calidad y seguridad aplicados."""

    __tablename__ = "bdoo_regla_validacion"

    regla_id = Column(Integer, primary_key=True, autoincrement=True)
    respuesta_id = Column(
        Integer, ForeignKey("bdoo_respuesta_agente.respuesta_id"), nullable=False
    )
    nombre_regla = Column(String(100), nullable=False)
    exitosa = Column(Boolean, nullable=False)
    observacion = Column(String(255))

    respuesta = relationship("RespuestaAgente", back_populates="reglas")


class AgenteAnalitico:
    """Registra una pregunta asociada a un usuario y una sesión existentes."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def procesar_pregunta(
        self, usuario_id: int, sesion_id: int, texto_pregunta: str
    ) -> Pregunta:
        texto = texto_pregunta.strip()
        if not texto:
            raise ValueError("La pregunta no puede estar vacía.")

        sesion = self.db.get(Sesion, sesion_id)
        if sesion is None:
            raise ValueError(f"No existe la sesión {sesion_id}.")
        if sesion.usuario_id != usuario_id:
            raise ValueError("La sesión indicada no pertenece al usuario.")
        if not sesion.activa:
            raise ValueError("No se pueden registrar preguntas en una sesión inactiva.")

        pregunta = Pregunta(sesion_id=sesion_id, texto_original=texto)
        self.db.add(pregunta)
        self.db.flush()
        return pregunta


@dataclass(frozen=True)
class Consulta:
    """Descripción de una consulta ejecutable por el agente."""

    identificador: str
    descripcion: str


@dataclass
class ResultadoEjecucion:
    """Resultado normalizado de una consulta del catálogo."""

    consulta: Consulta
    filas: list[dict[str, Any]] = field(default_factory=list)
    mensaje: str = ""


@dataclass
class RegistroTrazabilidad:
    """Evento de auditoría sin credenciales ni contenido de filas."""

    pregunta: str
    consulta_id: str
    estado: str
    duracion_ms: float
    detalle_error: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    creado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RespuestaEjecucion:
    """Respuesta inmediata de la CLI, independiente de la entidad ORM."""

    texto: str
    resultado: ResultadoEjecucion | None = None
    trazabilidad: RegistroTrazabilidad | None = None
