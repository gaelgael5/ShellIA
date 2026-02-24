# main.py

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict
from pathlib import Path
from datetime import timedelta
import os
import urllib.parse

from core.ai_chatgpt import ChatGPTProvider
from core.ai_claude import ClaudeProvider
from core.shell_executor import ShellExecutor
from core.context_store import ContextStore
from core.environment_manager import EnvironmentManager
from core.api_manager import APIManager
from core.profile_manager import ProfileManager
from core.auth import user_manager, create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Charger les variables d'environnement depuis le dossier environments/
try:
    from dotenv import load_dotenv

    # Déterminer quel environnement charger
    env_name = os.getenv("SHELLIA_ENV", "local")
    env_file = Path(__file__).parent.parent / "environments" / f"{env_name}.env"

    if env_file.exists():
        load_dotenv(env_file)
        env_display_name = os.getenv("ENV_NAME", env_name)
        env_description = os.getenv("ENV_DESCRIPTION", "")
        print(f"📝 Environnement chargé: {env_display_name}")
        if env_description:
            print(f"   {env_description}")
    else:
        fallback_env = Path(__file__).parent.parent / ".env"
        if fallback_env.exists():
            load_dotenv(fallback_env)
            print(f"📝 Fichier .env chargé (fallback)")
        else:
            print(f"⚠️  Aucun fichier d'environnement trouvé")
            print(f"   Fichier attendu: {env_file}")
            print(f"   Utilisez: set SHELLIA_ENV=local ou set SHELLIA_ENV=remote")
except ImportError:
    print("⚠️  python-dotenv non installé, utilisation des variables d'environnement système")
    print("   Installez avec: pip install python-dotenv")

# Importer les providers OAuth APRÈS load_dotenv pour que les variables soient disponibles
from core.google_auth import google_auth_provider
from core.microsoft_auth import microsoft_auth_provider
from core.facebook_auth import facebook_auth_provider

# ============================================================================
# Init app
# ============================================================================

app = FastAPI()

# Chemins de base
PROJECT_ROOT = Path(__file__).parent.parent
USERS_DIR = PROJECT_ROOT / "users"
GLOBAL_ENVIRONMENTS_DIR = PROJECT_ROOT / "environments"
GLOBAL_APIS_FILE = PROJECT_ROOT / "apis.json"

# Handler pour les erreurs de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print(f"❌ Erreur de validation pour {request.url}")
    print(f"   Body: {body}")
    print(f"   Erreurs: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body.decode()},
    )

# ============================================================================
# Sessions utilisateur (per-user state)
# ============================================================================

class UserSession:
    """Stocke l'état d'un utilisateur connecté (shell, IA, contexte)."""

    def __init__(self, email: str):
        self.email = email
        self.context_store = ContextStore()
        self.shell_executor = None
        self.ai_provider = None
        self.env_manager = EnvironmentManager(
            environments_dir=USERS_DIR / email / "environments"
        )
        self.api_manager = APIManager(
            config_file=USERS_DIR / email / "apis.json"
        )
        self.profile_manager = ProfileManager(
            profiles_file=USERS_DIR / email / "profiles.json"
        )

    def init_from_environment(self, env_name: str, ssh_password: Optional[str] = None):
        """Initialise shell_executor et ai_provider depuis un environnement."""
        # Charger les variables de l'environnement
        env_data = self.env_manager.get_environment(env_name)
        if not env_data:
            raise ValueError(f"Environnement {env_name} non trouvé")

        self.env_manager.load_environment(env_name)

        # Init Shell Executor
        execution_mode = env_data.get("EXECUTION_MODE", "local").lower()

        if execution_mode == "remote":
            ssh_host = env_data.get("SSH_HOST")
            ssh_user = env_data.get("SSH_USER")
            ssh_port = int(env_data.get("SSH_PORT", "22"))
            ssh_key_path = env_data.get("SSH_KEY_PATH")
            password = ssh_password or env_data.get("SSH_PASSWORD")

            if not ssh_host or not ssh_user:
                raise ValueError("SSH_HOST et SSH_USER doivent être définis en mode remote")

            self.shell_executor = ShellExecutor(
                mode="remote",
                ssh_host=ssh_host,
                ssh_user=ssh_user,
                ssh_port=ssh_port,
                ssh_key_path=ssh_key_path,
                ssh_password=password
            )
        elif execution_mode == "wsl":
            wsl_distribution = env_data.get("WSL_DISTRIBUTION", "")
            self.shell_executor = ShellExecutor(
                mode="wsl",
                wsl_distribution=wsl_distribution if wsl_distribution else None
            )
        else:
            self.shell_executor = ShellExecutor(mode="local")

        # Init AI Provider
        ai_api_id = env_data.get("AI_API_ID", "")

        if ai_api_id:
            api_config = self.api_manager.get_api(ai_api_id)
            if not api_config:
                raise ValueError(f"API {ai_api_id} non trouvée dans la configuration")

            ai_provider_type = api_config.get("provider", "chatgpt").lower()
            api_key = api_config.get("api_key", "")

            if not api_key:
                raise ValueError(f"Clé API manquante pour {ai_api_id}")

            if ai_provider_type == "claude":
                model = api_config.get("model", "claude-sonnet-4-20250514")
                self.ai_provider = ClaudeProvider(api_key=api_key, model=model)
            else:
                self.ai_provider = ChatGPTProvider(api_key=api_key)
        else:
            ai_provider_type = env_data.get("AI_PROVIDER", "chatgpt").lower()

            if ai_provider_type == "claude":
                api_key = env_data.get("ANTHROPIC_API_KEY", "")
                model = env_data.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
                if api_key:
                    self.ai_provider = ClaudeProvider(api_key=api_key, model=model)
            elif ai_provider_type == "chatgpt":
                api_key = env_data.get("OPENAI_API_KEY", "")
                if api_key:
                    self.ai_provider = ChatGPTProvider(api_key=api_key)

        return env_data


# Dict global des sessions utilisateur
user_sessions: dict[str, UserSession] = {}


def get_user_session(email: str) -> UserSession:
    """Récupère ou crée la session d'un utilisateur."""
    if email not in user_sessions:
        session = UserSession(email)
        # Essayer de charger le premier environnement disponible
        envs = session.env_manager.list_environments()
        if envs:
            try:
                session.init_from_environment(envs[0]["filename"])
                print(f"🔄 Session initialisée pour {email} avec env: {envs[0]['filename']}")
            except Exception as e:
                print(f"⚠️  Impossible d'initialiser la session pour {email}: {e}")
                # Session sans shell/ai - l'utilisateur devra charger un environnement
                session.shell_executor = ShellExecutor(mode="local")
        else:
            # Aucun environnement, mode local par défaut
            session.shell_executor = ShellExecutor(mode="local")
            print(f"🔄 Session locale créée pour {email} (aucun environnement)")

        user_sessions[email] = session

    return user_sessions[email]


# ============================================================================
# AUTHENTIFICATION
# ============================================================================

security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    token: str


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dépendance pour obtenir l'utilisateur courant depuis le token JWT."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token manquant")

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = user_manager.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")

    return user


# ============================================================================
# Pages HTML
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def index():
    """Sert la page principale (la protection se fait côté frontend + API)."""
    return open("ui/index.html", encoding="utf-8").read()


@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Sert la page de connexion."""
    return open("ui/login.html", encoding="utf-8").read()


# ============================================================================
# Endpoints d'authentification (non protégés)
# ============================================================================

@app.get("/auth/config")
def auth_config():
    """Retourne la configuration d'authentification (providers activés)."""
    return {
        "google_enabled": google_auth_provider.is_enabled(),
        "google_client_id": google_auth_provider.client_id if google_auth_provider.is_enabled() else None,
        "microsoft_enabled": microsoft_auth_provider.is_enabled(),
        "facebook_enabled": facebook_auth_provider.is_enabled(),
    }


@app.post("/auth/register")
def register(req: RegisterRequest):
    """Inscription d'un nouvel utilisateur."""
    try:
        user = user_manager.create_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name
        )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
def login(req: LoginRequest):
    """Connexion avec email et mot de passe."""
    user = user_manager.authenticate_user(req.email, req.password)

    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.post("/auth/google")
def google_login(req: GoogleAuthRequest):
    """Connexion avec Google OpenID."""
    if not google_auth_provider.is_enabled():
        raise HTTPException(status_code=400, detail="Authentification Google non configurée")

    google_user = google_auth_provider.verify_google_token(req.token)

    if not google_user:
        raise HTTPException(status_code=401, detail="Token Google invalide")

    if not google_user.get("email_verified"):
        raise HTTPException(status_code=400, detail="Email non vérifié")

    email = google_user["email"]
    google_id = google_user["google_id"]

    user = user_manager.get_user_by_email(email)

    if not user:
        try:
            user = user_manager.create_user(
                email=email,
                google_id=google_id,
                full_name=google_user.get("full_name")
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.get("/auth/microsoft/login")
def microsoft_login(request: Request):
    """Redirige vers la page de connexion Microsoft."""
    if not microsoft_auth_provider.is_enabled():
        raise HTTPException(status_code=400, detail="Authentification Microsoft non configurée")

    redirect_uri = str(request.base_url) + "auth/microsoft/callback"
    auth_url = microsoft_auth_provider.get_auth_url(redirect_uri)
    return RedirectResponse(url=auth_url)


@app.get("/auth/microsoft/callback")
def microsoft_callback(request: Request):
    """Callback après authentification Microsoft."""
    if not microsoft_auth_provider.is_enabled():
        raise HTTPException(status_code=400, detail="Authentification Microsoft non configurée")

    redirect_uri = str(request.base_url) + "auth/microsoft/callback"
    query_params = dict(request.query_params)

    ms_user = microsoft_auth_provider.verify_microsoft_callback(query_params, redirect_uri)

    if not ms_user:
        return RedirectResponse(url="/login?error=microsoft_auth_failed")

    email = ms_user["email"]
    microsoft_id = ms_user.get("microsoft_id")

    # Vérifier si l'utilisateur existe déjà
    user = user_manager.get_user_by_email(email)

    if not user:
        # Créer un nouvel utilisateur
        try:
            user = user_manager.create_user(
                email=email,
                google_id=microsoft_id,  # Réutilise le champ google_id pour stocker l'ID externe
                full_name=ms_user.get("full_name")
            )
        except ValueError as e:
            return RedirectResponse(url=f"/login?error={str(e)}")

    # Créer un token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    return RedirectResponse(
        url=f"/login?token={access_token}&user_email={urllib.parse.quote(user['email'])}&user_name={urllib.parse.quote(user.get('full_name') or '')}"
    )


@app.get("/auth/facebook/login")
def facebook_login(request: Request):
    """Redirige vers la page de connexion Facebook."""
    if not facebook_auth_provider.is_enabled():
        raise HTTPException(status_code=400, detail="Authentification Facebook non configurée")

    redirect_uri = str(request.base_url) + "auth/facebook/callback"
    auth_url = facebook_auth_provider.get_auth_url(redirect_uri)
    return RedirectResponse(url=auth_url)


@app.get("/auth/facebook/callback")
def facebook_callback(request: Request):
    """Callback après authentification Facebook."""
    if not facebook_auth_provider.is_enabled():
        raise HTTPException(status_code=400, detail="Authentification Facebook non configurée")

    redirect_uri = str(request.base_url) + "auth/facebook/callback"
    code = request.query_params.get("code")

    if not code:
        error = request.query_params.get("error_description", "Authentification annulée")
        return RedirectResponse(url=f"/login?error={urllib.parse.quote(error)}")

    fb_user = facebook_auth_provider.verify_facebook_callback(code, redirect_uri)

    if not fb_user:
        return RedirectResponse(url="/login?error=facebook_auth_failed")

    email = fb_user["email"]

    # Vérifier si l'utilisateur existe déjà
    user = user_manager.get_user_by_email(email)

    if not user:
        try:
            user = user_manager.create_user(
                email=email,
                google_id=fb_user.get("facebook_id"),
                full_name=fb_user.get("full_name")
            )
        except ValueError as e:
            return RedirectResponse(url=f"/login?error={urllib.parse.quote(str(e))}")

    # Créer un token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    return RedirectResponse(
        url=f"/login?token={access_token}&user_email={urllib.parse.quote(user['email'])}&user_name={urllib.parse.quote(user.get('full_name') or '')}"
    )


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Retourne l'utilisateur courant."""
    return current_user


# ============================================================================
# Endpoints protégés - IA et Exécution
# ============================================================================

class AiRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict]] = None
    profile_id: Optional[str] = None


class ExecuteRequest(BaseModel):
    command: str


@app.post("/ai/suggest")
def ai_suggest(req: AiRequest, current_user: dict = Depends(get_current_user)):
    session = get_user_session(current_user["email"])
    if not session.ai_provider:
        raise HTTPException(status_code=400, detail="Aucun provider IA configuré. Chargez un environnement.")

    context = session.context_store.get()
    chat_history = req.chat_history or []

    # Récupérer le prompt du profil actif si spécifié
    system_profile = None
    if req.profile_id:
        profile = session.profile_manager.get_profile(req.profile_id)
        if profile:
            system_profile = profile.get("prompt")

    result = session.ai_provider.ask(
        context=context,
        user_message=req.message,
        chat_history=chat_history,
        system_profile=system_profile
    )
    return result


@app.post("/execute")
def execute(req: ExecuteRequest, current_user: dict = Depends(get_current_user)):
    session = get_user_session(current_user["email"])
    if not session.shell_executor:
        raise HTTPException(status_code=400, detail="Aucun shell configuré. Chargez un environnement.")
    result = session.shell_executor.execute(req.command)
    session.context_store.add(req.command, result["stdout"], result["stderr"])
    return result


# ============================================================================
# Endpoints protégés - Gestion des APIs IA
# ============================================================================

class APIData(BaseModel):
    data: dict


@app.get("/apis")
def list_apis(current_user: dict = Depends(get_current_user)):
    """Liste toutes les APIs IA configurées pour l'utilisateur."""
    session = get_user_session(current_user["email"])
    return session.api_manager.list_apis()


@app.get("/apis/{api_id}")
def get_api(api_id: str, current_user: dict = Depends(get_current_user)):
    """Récupère les détails d'une API."""
    session = get_user_session(current_user["email"])
    api_data = session.api_manager.get_api(api_id)
    if api_data is None:
        raise HTTPException(status_code=404, detail="API non trouvée")
    return api_data


@app.post("/apis/{api_id}")
def create_api(api_id: str, payload: APIData, current_user: dict = Depends(get_current_user)):
    """Crée une nouvelle configuration API."""
    session = get_user_session(current_user["email"])
    api_data = payload.data
    api_data["id"] = api_id
    success = session.api_manager.create_api(api_data)
    return {"success": success, "message": "API créée" if success else "Échec de la création"}


@app.put("/apis/{api_id}")
def update_api(api_id: str, payload: APIData, current_user: dict = Depends(get_current_user)):
    """Met à jour une API existante."""
    session = get_user_session(current_user["email"])
    success = session.api_manager.update_api(api_id, payload.data)
    return {"success": success, "message": "API mise à jour" if success else "Échec de la mise à jour"}


@app.delete("/apis/{api_id}")
def delete_api(api_id: str, current_user: dict = Depends(get_current_user)):
    """Supprime une API."""
    session = get_user_session(current_user["email"])
    success = session.api_manager.delete_api(api_id)
    return {"success": success, "message": "API supprimée" if success else "Échec de la suppression"}


# ============================================================================
# Endpoints protégés - Gestion des Environnements
# ============================================================================

class EnvironmentData(BaseModel):
    data: dict


@app.get("/environments")
def list_environments(current_user: dict = Depends(get_current_user)):
    """Liste tous les environnements disponibles pour l'utilisateur."""
    session = get_user_session(current_user["email"])
    return session.env_manager.list_environments()


@app.get("/environments/{env_name}")
def get_environment(env_name: str, current_user: dict = Depends(get_current_user)):
    """Récupère les détails d'un environnement."""
    session = get_user_session(current_user["email"])
    env_data = session.env_manager.get_environment(env_name)
    if env_data is None:
        raise HTTPException(status_code=404, detail="Environnement non trouvé")
    return env_data


@app.post("/environments/{env_name}")
def create_environment(env_name: str, env_data: EnvironmentData, current_user: dict = Depends(get_current_user)):
    """Crée un nouvel environnement."""
    session = get_user_session(current_user["email"])
    success = session.env_manager.create_environment(env_name, env_data.data)
    if success:
        return {"success": True, "message": f"Environnement {env_name} créé"}
    else:
        return {"success": False, "message": "Erreur lors de la création"}


@app.put("/environments/{env_name}")
def update_environment(env_name: str, env_data: EnvironmentData, current_user: dict = Depends(get_current_user)):
    """Met à jour un environnement existant."""
    session = get_user_session(current_user["email"])
    success = session.env_manager.update_environment(env_name, env_data.data)
    if success:
        return {"success": True, "message": f"Environnement {env_name} mis à jour"}
    else:
        return {"success": False, "message": "Erreur lors de la mise à jour"}


@app.delete("/environments/{env_name}")
def delete_environment(env_name: str, current_user: dict = Depends(get_current_user)):
    """Supprime un environnement."""
    session = get_user_session(current_user["email"])
    success = session.env_manager.delete_environment(env_name)
    if success:
        return {"success": True, "message": f"Environnement {env_name} supprimé"}
    else:
        return {"success": False, "message": "Impossible de supprimer l'environnement"}


class LoadEnvironmentBody(BaseModel):
    ssh_password: Optional[str] = None


@app.post("/environments/load-v2/{env_name}")
def load_environment(env_name: str, body: LoadEnvironmentBody = LoadEnvironmentBody(),
                     current_user: dict = Depends(get_current_user)):
    """Charge un environnement (redémarre les composants) pour l'utilisateur courant."""
    email = current_user["email"]
    session = get_user_session(email)

    print(f"🔄 Chargement de l'environnement: {env_name} pour {email}")

    try:
        env_data = session.init_from_environment(env_name, ssh_password=body.ssh_password)

        execution_mode = env_data.get("EXECUTION_MODE", "local").lower()
        response = {
            "success": True,
            "message": f"Environnement {env_name} chargé",
            "env_name": env_data.get("ENV_NAME", env_name),
            "execution_mode": execution_mode
        }

        ai_api_id = env_data.get("AI_API_ID", "")
        if ai_api_id:
            api_config = session.api_manager.get_api(ai_api_id)
            if api_config:
                response["ai_provider"] = api_config.get("provider")
                response["ai_api_name"] = api_config.get("name")
                response["ai_model"] = api_config.get("model", "")
        else:
            response["ai_provider"] = env_data.get("AI_PROVIDER", "chatgpt")

        return response

    except Exception as e:
        print(f"❌ Erreur lors du chargement de l'environnement: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}

# ============================================================================
# Endpoints protégés - Gestion des Profils IA
# ============================================================================

class ProfileData(BaseModel):
    data: dict


@app.get("/profiles")
def list_profiles(current_user: dict = Depends(get_current_user)):
    """Liste tous les profils IA de l'utilisateur."""
    session = get_user_session(current_user["email"])
    return session.profile_manager.list_profiles()


@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str, current_user: dict = Depends(get_current_user)):
    session = get_user_session(current_user["email"])
    profile = session.profile_manager.get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    return profile


@app.post("/profiles/{profile_id}")
def create_profile(profile_id: str, payload: ProfileData, current_user: dict = Depends(get_current_user)):
    session = get_user_session(current_user["email"])
    data = payload.data
    data["id"] = profile_id
    success = session.profile_manager.create_profile(data)
    return {"success": success, "message": "Profil créé" if success else "ID déjà utilisé"}


@app.put("/profiles/{profile_id}")
def update_profile(profile_id: str, payload: ProfileData, current_user: dict = Depends(get_current_user)):
    session = get_user_session(current_user["email"])
    success = session.profile_manager.update_profile(profile_id, payload.data)
    return {"success": success, "message": "Profil mis à jour" if success else "Profil non trouvé"}


@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str, current_user: dict = Depends(get_current_user)):
    session = get_user_session(current_user["email"])
    success = session.profile_manager.delete_profile(profile_id)
    return {"success": success, "message": "Profil supprimé" if success else "Profil non trouvé"}
