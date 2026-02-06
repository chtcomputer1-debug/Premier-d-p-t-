# config.py - MISES À JOUR
import os
import sqlite3
from hashlib import sha256

class Config:
    # Configuration base de données
    DB_NAME = 'intercht.db'
    
    # Mot de passe admin
    ADMIN_USERNAME = 'bilunu'
    ADMIN_PASSWORD_HASH = sha256('paul26'.encode()).hexdigest()
    
    # Dossier uploads pour images
    UPLOAD_FOLDER = 'static/uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Extensions autorisées
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}
    
    @staticmethod
    def init_database():
        """Initialiser la base de données avec nouvelles tables"""
        conn = sqlite3.connect(Config.DB_NAME)
        cursor = conn.cursor()
        
        # Table services (EXISTANTE)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icon TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            details TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # NOUVELLE TABLE : service_media
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,  -- 'image' ou 'video'
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
        )
        ''')
        
        # Table contacts (EXISTANTE)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            message TEXT NOT NULL,
            service_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services (id)
        )
        ''')
        
        # Table admin_log (EXISTANTE)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Vérifier si services existent
        cursor.execute('SELECT COUNT(*) FROM services')
        if cursor.fetchone()[0] == 0:
            # Insérer vos services exacts
            services = [
                ('🖥️', 'SYSTÈME', 'Installation et configuration de systèmes',
                 '''• Installation Windows (7, 8, 10, 11)
• Activation Windows
• Installation Ubuntu/Linux
• Configuration dual-boot (Windows/Linux)''', None),
                
                ('📁', 'BUREAUTIQUE', 'Suites bureautiques et productivité',
                 '''• Installation Microsoft Office
   - Word, Excel, PowerPoint, etc.
• Installation suites alternatives
• Services bureautiques (saisies documents: CV, lettres, ...) ''', None),
                
                ('🛡️', 'SÉCURITÉ', 'Protection et maintenance système',
                 '''• Installation anti-virus
• Logiciels de sécurité
• Optimisation système
• Nettoyage disque
• Sauvegarde de données
• Récupération fichiers''', None),
                
                ('💻', 'DÉVELOPPEMENT', 'Environnements de développement',
                 '''ENVIRONNEMENTS :
• Python + bibliothèques
• Java (JDK + NetBeans)
• Dev-C++ / Code::Blocks
• Visual Studio Code / Cursor
• PHP + XAMP
• HTML / CSS / JavaScript
BASES DE DONNÉES :
• MySQL
• SQLite''', None),
                
                ('🎮', 'JEUX VIDÉO', 'Installation, émulation et optimisation',
                 '''ÉMULATION CONSOLES :
• PlayStation Portable (PPSSPP)
• PlayStation 2 (PCSX2)
• PlayStation 3 (RPCS3)
JEUX PC :
• Installation et configuration complète
• Résolution problèmes de comptabilité
• Optimisation des performances
• Mise à jour et gestion des pilotes''', None),
                
                ('🎨', 'CREATION & MULTIMÉDIA', 'Installation et conversion',
                 '''• Installation Photoshop (2021, 2024), Canva
• Logiciels multimédia :
   - VLC, Virtual DJ
   - Audacity, HandBrake
• Conversion formats :
   - Vidéo (MP4, AVI, MKV)
   - Audio (MP3, FLAC, WAV)
   - Images (JPEG, PNG, GIF, WEBP)''', None),
                
                ('🌐', 'INTERNET', 'Navigation et configuration réseau',
                 '''• Installation navigateurs :
   - Firefox, Chrome, Microsoft Edge
   - Opéra, Brave, DuckDuckGo
• Configuration réseau
• Sécurité réseau
    - Configuration VPN et proxy
    - Protection navigation ''', None),
                
                ('🎬', 'DIVERTISSEMENT', 'Gestion contenus de détente',
                 '''• Organisation bibliothèques :
   - Films et séries
   - Musique
• Conversion multimédias
• Mangas / BD numériques''', None),
                
                ('🔧', 'SERVICES +', 'Services supplémentaires',
                 '''• Installation drivers
• Mises à jour système
• Résolution problèmes
• Diagnostic matériel
• Formation logiciels
• Conseils personnalisés
• Support technique''', None)
            ]
            
            cursor.executemany('''
            INSERT INTO services (icon, title, description, details, image_path)
            VALUES (?, ?, ?, ?, ?)
            ''', services)
            
            cursor.execute("INSERT INTO admin_log (action) VALUES ('Base de données initialisée')")
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def verify_admin(username, password):
        """Vérifier les identifiants admin"""
        if username != Config.ADMIN_USERNAME:
            return False
        password_hash = sha256(password.encode()).hexdigest()
        return password_hash == Config.ADMIN_PASSWORD_HASH
    
    @staticmethod
    def allowed_file(filename):
        """Vérifier si le fichier est autorisé"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Initialiser la base au démarrage
Config.init_database()