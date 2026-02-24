# core/auth.py

import sqlite3
import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "votre-cle-secrete-a-changer-en-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Chemin de la base de données
DB_PATH = Path(__file__).parent.parent.parent / "data" / "users.db"


class UserManager:
    """Gestionnaire des utilisateurs avec SQLite."""

    def __init__(self):
        """Initialise la base de données."""
        # Créer le répertoire data s'il n'existe pas
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Créer la table users si elle n'existe pas
        self._init_db()

    def _init_db(self):
        """Initialise la base de données avec les tables nécessaires."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT,
                full_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_google_auth BOOLEAN DEFAULT 0,
                google_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

    def get_password_hash(self, password: str) -> str:
        """Hache un mot de passe."""
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def create_user(self, email: str, password: Optional[str] = None,
                   full_name: Optional[str] = None, google_id: Optional[str] = None) -> dict:
        """
        Crée un nouvel utilisateur.

        Args:
            email: Email de l'utilisateur
            password: Mot de passe (optionnel si google_id fourni)
            full_name: Nom complet (optionnel)
            google_id: ID Google (pour authentification Google)

        Returns:
            Dictionnaire avec les informations de l'utilisateur
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                raise ValueError("Cet email est déjà utilisé")

            # Hacher le mot de passe si fourni
            hashed_password = self.get_password_hash(password) if password else None
            is_google_auth = google_id is not None

            # Insérer l'utilisateur
            cursor.execute("""
                INSERT INTO users (email, hashed_password, full_name, is_google_auth, google_id)
                VALUES (?, ?, ?, ?, ?)
            """, (email, hashed_password, full_name, is_google_auth, google_id))

            conn.commit()
            user_id = cursor.lastrowid

            # Créer le répertoire utilisateur
            self._create_user_directory(email)

            # Retourner les informations de l'utilisateur
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = dict(cursor.fetchone())

            return self._user_dict(user)

        except sqlite3.IntegrityError as e:
            raise ValueError(f"Erreur lors de la création de l'utilisateur: {e}")
        finally:
            conn.close()

    def _create_user_directory(self, email: str):
        """Crée la structure de répertoires pour un utilisateur et copie les données globales."""
        user_dir = self._get_user_directory(email)
        user_dir.mkdir(parents=True, exist_ok=True)

        project_root = Path(__file__).parent.parent.parent

        # Créer le sous-répertoire environments et copier les envs globaux
        env_dir = user_dir / "environments"
        env_dir.mkdir(exist_ok=True)

        global_env_dir = project_root / "environments"
        if global_env_dir.exists():
            for env_file in global_env_dir.glob("*.env"):
                if env_file.name in ["template.env", ".env.example"]:
                    continue
                dest = env_dir / env_file.name
                if not dest.exists():
                    shutil.copy2(env_file, dest)

        # Copier le apis.json global ou créer un fichier vide
        apis_file = user_dir / "apis.json"
        if not apis_file.exists():
            global_apis = project_root / "apis.json"
            if global_apis.exists():
                shutil.copy2(global_apis, apis_file)
            else:
                apis_file.write_text('{"apis": []}', encoding="utf-8")

    def _get_user_directory(self, email: str) -> Path:
        """Retourne le chemin du répertoire utilisateur."""
        users_dir = Path(__file__).parent.parent.parent / "users"
        return users_dir / email

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Récupère un utilisateur par son email."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        return self._user_dict(dict(user)) if user else None

    def get_user_by_google_id(self, google_id: str) -> Optional[dict]:
        """Récupère un utilisateur par son Google ID."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
        user = cursor.fetchone()
        conn.close()

        return self._user_dict(dict(user)) if user else None

    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authentifie un utilisateur avec email et mot de passe."""
        # Récupérer l'utilisateur avec le hash (sans passer par _user_dict)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        user = dict(row)

        if not user.get("hashed_password"):
            # Utilisateur Google sans mot de passe
            return None

        if not self.verify_password(password, user["hashed_password"]):
            return None

        # Mettre à jour last_login
        self._update_last_login(email)

        return self._user_dict(user)

    def _update_last_login(self, email: str):
        """Met à jour la date de dernière connexion."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (email,))

        conn.commit()
        conn.close()

    def _user_dict(self, user: dict) -> dict:
        """Convertit un utilisateur en dictionnaire sans le mot de passe."""
        if not user:
            return None

        return {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "is_active": bool(user["is_active"]),
            "is_google_auth": bool(user["is_google_auth"]),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        }


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Vérifie un token JWT et retourne les données."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# Instance globale
user_manager = UserManager()
