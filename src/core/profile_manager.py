# core/profile_manager.py

import json
from pathlib import Path
from typing import List, Dict, Optional


class ProfileManager:
    """Gère les profils de prompt IA par utilisateur."""

    def __init__(self, profiles_file: Path):
        self.profiles_file = profiles_file
        self.profiles_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> List[Dict]:
        if not self.profiles_file.exists():
            return []
        with open(self.profiles_file, encoding='utf-8') as f:
            return json.load(f)

    def _save(self, profiles: List[Dict]):
        with open(self.profiles_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)

    def list_profiles(self) -> List[Dict]:
        return self._load()

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        for p in self._load():
            if p.get('id') == profile_id:
                return p
        return None

    def create_profile(self, data: Dict) -> bool:
        profiles = self._load()
        # Vérifier que l'ID n'existe pas déjà
        if any(p.get('id') == data.get('id') for p in profiles):
            return False
        profiles.append(data)
        self._save(profiles)
        return True

    def update_profile(self, profile_id: str, data: Dict) -> bool:
        profiles = self._load()
        for i, p in enumerate(profiles):
            if p.get('id') == profile_id:
                profiles[i] = {**p, **data, 'id': profile_id}
                self._save(profiles)
                return True
        return False

    def delete_profile(self, profile_id: str) -> bool:
        profiles = self._load()
        new_profiles = [p for p in profiles if p.get('id') != profile_id]
        if len(new_profiles) < len(profiles):
            self._save(new_profiles)
            return True
        return False
