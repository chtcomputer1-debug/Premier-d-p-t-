# serv.py - VERSION FINALE
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from config import Config

app = Flask(__name__)
app.secret_key = 'cht_computer_secret_2026'
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

# ========== FONCTIONS BASE DE DONNÉES ==========

def get_db_connection():
    conn = sqlite3.connect(Config.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_services():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM services ORDER BY id')
    services = cursor.fetchall()
    conn.close()
    return services

def get_service_by_id(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM services WHERE id = ?', (service_id,))
    service = cursor.fetchone()
    conn.close()
    return service

def get_service_media(service_id):
    """Récupérer TOUS les médias d'un service"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM service_media 
        WHERE service_id = ? 
        ORDER BY uploaded_at DESC
    ''', (service_id,))
    media = cursor.fetchall()
    conn.close()
    return media

def add_media_to_service(service_id, filename, file_type='image'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO service_media (service_id, filename, file_type)
        VALUES (?, ?, ?)
    ''', (service_id, filename, file_type))
    conn.commit()
    conn.close()

def add_contact(name, email, phone, message, service_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contacts (name, email, phone, message, service_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, email, phone, message, service_id))
    conn.commit()
    conn.close()

def get_all_contacts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, s.title as service_title
        FROM contacts c
        LEFT JOIN services s ON c.service_id = s.id
        ORDER BY c.created_at DESC
    ''')
    contacts = cursor.fetchall()
    conn.close()
    return contacts

# ========== ROUTES PRINCIPALES ==========

@app.route('/')
def index():
    services = get_all_services()
    return render_template('index.html', services=services)

@app.route('/service/<int:service_id>')
def service_detail(service_id):
    service = get_service_by_id(service_id)
    if not service:
        return redirect(url_for('index'))
    
    media = get_service_media(service_id)
    return render_template('service_detail.html', service=service, media=media)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    services = get_all_services()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()
        service_id = request.form.get('service_id')

        if not name or not phone or not message:
            return render_template('contact.html',
                                 services=services,
                                 error='Veuillez remplir tous les champs obligatoires')

        add_contact(name, email, phone, message, service_id)
        return render_template('contact.html',
                             services=services,
                             success='Message envoyé avec succès!')
    
    return render_template('contact.html', services=services)

# ========== ROUTES ADMIN ==========

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if Config.verify_admin(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Identifiants incorrects')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    contacts = get_all_contacts()
    services = get_all_services()
    
    # Récupérer tous les médias
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM service_media')
    media_list = cursor.fetchall()
    conn.close()
    
    # Log
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO admin_log (action) VALUES ('Accès panneau admin')")
    conn.commit()
    conn.close()
    
    return render_template('admin.html',
                          contacts=contacts,
                          services=services,
                          media_list=media_list,
                          username=session.get('admin_username'))

# ========== ROUTES GESTION DES MÉDIAS ==========

@app.route('/admin/media/<int:service_id>', methods=['GET'])
def admin_media(service_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    service = get_service_by_id(service_id)
    if not service:
        return redirect(url_for('admin_panel'))
    
    media = get_service_media(service_id)
    return render_template('admin_media.html', service=service, media=media)

@app.route('/admin/media/<int:service_id>/upload', methods=['POST'])
def admin_upload_media(service_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Non autorisé'}), 403
    
    if 'files[]' not in request.files:
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    files = request.files.getlist('files[]')
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        if file and Config.allowed_file(file.filename):
            filename = file.filename
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            file_type = 'video' if extension in {'mp4', 'avi', 'mov', 'webm'} else 'image'
            
            unique_filename = f"media_{service_id}_{os.urandom(4).hex()}.{extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            file.save(file_path)
            add_media_to_service(service_id, unique_filename, file_type)
            
            uploaded_files.append({
                'filename': unique_filename,
                'type': file_type,
                'url': url_for('static', filename=f'uploads/{unique_filename}')
            })
    
    return jsonify({
        'success': True,
        'message': f'{len(uploaded_files)} fichier(s) uploadé(s)',
        'files': uploaded_files
    })

@app.route('/admin/media/<int:media_id>/delete', methods=['POST'])
def admin_delete_media(media_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT filename, service_id FROM service_media WHERE id = ?', (media_id,))
    media = cursor.fetchone()
    
    if media:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], media['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        cursor.execute('DELETE FROM service_media WHERE id = ?', (media_id,))
        conn.commit()
        
        cursor.execute("INSERT INTO admin_log (action) VALUES (?)", 
                      (f'Suppression média {media["filename"]}',))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Média supprimé'
    })

# ========== ROUTES API ==========

@app.route('/api/services')
def api_services():
    services = get_all_services()
    services_list = []
    
    for service in services:
        services_list.append({
            'id': service['id'],
            'icon': service['icon'],
            'title': service['title'],
            'description': service['description'],
            'details': service['details']
        })
    
    return jsonify(services_list)

@app.route('/api/service/<int:service_id>/media')
def api_service_media(service_id):
    media = get_service_media(service_id)
    media_list = []
    
    for item in media:
        media_list.append({
            'id': item['id'],
            'filename': item['filename'],
            'file_type': item['file_type'],
            'url': url_for('static', filename=f'uploads/{item["filename"]}'),
            'uploaded_at': item['uploaded_at']
        })
    
    return jsonify(media_list)

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    message = data.get('message', '').strip()
    
    if not name or not email or not message:
        return jsonify({'error': 'Champs obligatoires manquants'}), 400
    
    add_contact(name, email, data.get('phone', ''), message, data.get('service_id'))
    return jsonify({'success': True, 'message': 'Message envoyé'})
# Suppression des messages
@app.route('/admin/message/<int:message_id>/delete', methods=['POST'])
def admin_delete_message(message_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contacts WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Message supprimé'})



# ========== LANCEMENT ==========

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════╗
    ║ 💦 CHT COMPUTER - SERVEUR WEB ║
    ║ URL : http://localhost:5008 ║
    ║ Admin : /admin/login ║
    ║ Mot de passe : ******** ║
    ╚══════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5008, debug=True)
