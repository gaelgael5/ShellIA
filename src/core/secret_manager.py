class SecretManager:
    def __init__(self):
        self.secrets = {}  # {alias: valeur}

    def add_secret(self, alias: str, value: str):
        """Stocke un secret avec un alias"""
        self.secrets[alias] = value

    def replace_in_command(self, command: str) -> str:
        """Remplace {{alias}} par la valeur réelle"""
        for alias, value in self.secrets.items():
            command = command.replace(f"{{{{{alias}}}}}", value)
        return command

    def get_prompt_hints(self) -> str:
        """Retourne la liste des alias disponibles pour l'IA"""
        return "Secrets disponibles: " + ", ".join([f"{{{{{k}}}}}" for k in self.secrets.keys()])


# Instance singleton par défaut
_default_manager = SecretManager()


def replace_in_command(command: str) -> str:
    """Fonction utilitaire qui utilise le manager par défaut"""
    return _default_manager.replace_in_command(command)
    