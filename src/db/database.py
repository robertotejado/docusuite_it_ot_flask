# src/db/database.py
import sqlite3
import os

# Definimos la ruta de la base de datos dentro del directorio del proyecto
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docusuite.db')

def get_db_connection():
    """Establece y retorna la conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    # Permite acceder a las columnas por nombre como si fueran diccionarios
    conn.row_factory = sqlite3.Row 
    # Activa las llaves foráneas para permitir el borrado en cascada
    conn.execute('PRAGMA foreign_keys = ON') 
    return conn

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabla de Proyectos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('IT', 'OT')) NOT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Tabla de Documentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_proyecto INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            autor TEXT,
            contenido_texto TEXT,
            fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_proyecto) REFERENCES proyectos (id) ON DELETE CASCADE
        )
    ''')

    # 3. Tabla de Adjuntos (Rutas locales para no saturar la BD)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adjuntos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_documento INTEGER NOT NULL,
            tipo_archivo TEXT NOT NULL,
            ruta_local TEXT NOT NULL,
            fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_documento) REFERENCES documentos (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print(f"[OK] Base de datos inicializada en: {DB_PATH}")

# Script de prueba rápida para inicializar al ejecutar directamente este archivo
if __name__ == '__main__':
    init_db()