class ProfileManager:
    def __init__(self):
        self.profiles = {
            "default": "Tu es un assistant d'administration Linux généraliste.",
            "proxmox": "Tu es spécialisé dans l'administration Proxmox (VM, containers LXC).",
            "docker": "Tu es spécialisé dans Docker et les conteneurs.",
            "rescue": "Tu es en mode rescue Linux, focus sur le diagnostic et la récupération."
        }
        self.active_profile = "default"
    
    def get_system_prompt(self, profile_name: str) -> str:
        return self.profiles.get(profile_name, self.profiles["default"])
    
    def add_profile(self, name: str, prompt: str):
        self.profiles[name] = prompt