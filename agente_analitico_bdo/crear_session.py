"""Script para registrar el Usuario Gerencial y la Sesión Inicial en la BDOO."""

from database import SessionLocal
from models_bdoo import Usuario, Sesion

def crear_usuario_y_sesion():
    db = SessionLocal()
    try:
        # 1. Registrar usuario gerencial
        usuario = Usuario(nombre="Gerente General", rol="Gerencia")
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # 2. Registrar sesión activa de trazabilidad
        sesion = Sesion(usuario_id=usuario.usuario_id, activa=True)
        db.add(sesion)
        db.commit()
        db.refresh(sesion)

        print(f"✓ Usuario registrado exitosamente: ID {usuario.usuario_id} ({usuario.nombre})")
        print(f"✓ Sesión activa registrada: ID {sesion.sesion_id}")

    finally:
        db.close()

if __name__ == "__main__":
    crear_usuario_y_sesion()