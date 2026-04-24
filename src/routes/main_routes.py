# src/routes/main_routes.py
import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify
from src.db.database import get_db_connection
from src.utils.exporters import export_document

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def splash():
    """Pantalla de carga inicial (Splash Screen)."""
    return render_template('splash.html')

@main_bp.route('/dashboard')
def dashboard():
    """Panel principal de la Suite."""
    conn = get_db_connection()
    proyectos = conn.execute('SELECT * FROM proyectos ORDER BY fecha_creacion DESC').fetchall()
    documentos = conn.execute('SELECT * FROM documentos ORDER BY fecha_modificacion DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', proyectos=proyectos, documentos=documentos)

# --- CRUD DE PROYECTOS ---
@main_bp.route('/proyectos', methods=['GET', 'POST'])
def gestion_proyectos():
    """Panel CRUD para crear, listar y actualizar Proyectos."""
    conn = get_db_connection()
    if request.method == 'POST':
        accion = request.form.get('action')
        if accion == 'crear':
            nombre = request.form['nombre']
            tipo = request.form['tipo']
            conn.execute('INSERT INTO proyectos (nombre, tipo) VALUES (?, ?)', (nombre, tipo))
        elif accion == 'actualizar':
            id_proy = request.form['id']
            nombre = request.form['nombre']
            tipo = request.form['tipo']
            conn.execute('UPDATE proyectos SET nombre = ?, tipo = ? WHERE id = ?', (nombre, tipo, id_proy))
        
        conn.commit()
        return redirect(url_for('main.gestion_proyectos'))

    proyectos = conn.execute('SELECT * FROM proyectos ORDER BY fecha_creacion DESC').fetchall()
    conn.close()
    return render_template('proyectos.html', proyectos=proyectos)

@main_bp.route('/proyectos/eliminar/<int:id>', methods=['POST'])
def eliminar_proyecto(id):
    """Elimina un proyecto (Borrado en cascada de sus documentos y adjuntos)."""
    conn = get_db_connection()
    conn.execute('DELETE FROM proyectos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('main.gestion_proyectos'))

# --- CRUD DE DOCUMENTOS ---
@main_bp.route('/documentos', methods=['GET', 'POST'])
def gestion_documentos():
    """Panel CRUD para listar, actualizar metadatos y eliminar Documentos."""
    conn = get_db_connection()
    
    if request.method == 'POST':
        accion = request.form.get('action')
        if accion == 'actualizar_meta':
            id_doc = request.form['id']
            titulo = request.form['titulo']
            id_proyecto = request.form['id_proyecto']
            conn.execute('UPDATE documentos SET titulo = ?, id_proyecto = ? WHERE id = ?', 
                         (titulo, id_proyecto, id_doc))
            conn.commit()
        return redirect(url_for('main.gestion_documentos'))

    documentos = conn.execute('''
        SELECT d.*, p.nombre as proyecto_nombre 
        FROM documentos d 
        LEFT JOIN proyectos p ON d.id_proyecto = p.id 
        ORDER BY d.fecha_modificacion DESC
    ''').fetchall()
    
    proyectos = conn.execute('SELECT * FROM proyectos').fetchall()
    conn.close()
    return render_template('documentos.html', documentos=documentos, proyectos=proyectos)

@main_bp.route('/documentos/eliminar/<int:id>', methods=['POST'])
def eliminar_documento(id):
    """Elimina un documento de la base de datos."""
    conn = get_db_connection()
    conn.execute('DELETE FROM documentos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('main.gestion_documentos'))

# --- EDITOR CENTRAL ---
@main_bp.route('/editor', methods=['GET', 'POST'])
@main_bp.route('/editor/<int:id_doc>', methods=['GET', 'POST'])
def editor(id_doc=None):
    """Editor TinyMCE para crear o actualizar el contenido de los documentos."""
    conn = get_db_connection()
    if request.method == 'POST':
        id_proyecto = request.form['id_proyecto']
        titulo = request.form['titulo']
        autor = request.form['autor']
        contenido = request.form['contenido_texto']
        doc_id_form = request.form.get('id_doc') 
        
        if doc_id_form:
            # Actualizamos documento existente
            conn.execute('''UPDATE documentos 
                            SET id_proyecto = ?, titulo = ?, autor = ?, contenido_texto = ?, fecha_modificacion = CURRENT_TIMESTAMP 
                            WHERE id = ?''', 
                         (id_proyecto, titulo, autor, contenido, doc_id_form))
        else:
            # Creamos uno nuevo
            conn.execute('INSERT INTO documentos (id_proyecto, titulo, autor, contenido_texto) VALUES (?, ?, ?, ?)', 
                         (id_proyecto, titulo, autor, contenido))
            
        conn.commit()
        conn.close()
        return redirect(url_for('main.gestion_documentos'))

    proyectos = conn.execute('SELECT * FROM proyectos').fetchall()
    doc_actual = None
    if id_doc:
        doc_actual = conn.execute('SELECT * FROM documentos WHERE id = ?', (id_doc,)).fetchone()
        
    conn.close()
    return render_template('editor.html', proyectos=proyectos, doc_actual=doc_actual)

# --- UTILIDADES ADICIONALES ---
@main_bp.route('/upload_attachment', methods=['POST'])
def upload_attachment():
    """Recibe la imagen de TinyMCE y devuelve la ruta JSON requerida."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f"img_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join('static', 'attachments', filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)
    
    return jsonify({'location': f"/static/attachments/{filename}"})

@main_bp.route('/exportar/<int:id_doc>/<formato>')
def exportar(id_doc, formato):
    """Genera y descarga el documento en el formato solicitado."""
    conn = get_db_connection()
    doc = conn.execute('SELECT * FROM documentos WHERE id = ?', (id_doc,)).fetchone()
    conn.close()
    
    if not doc:
        return "Documento no encontrado", 404
        
    filepath = export_document(dict(doc), formato)
    return send_file(filepath, as_attachment=True)