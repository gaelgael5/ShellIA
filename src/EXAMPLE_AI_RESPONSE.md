# Exemple de réponse IA au format Markdown

Ce fichier montre comment l'IA devrait formater ses réponses pour être correctement affichées dans l'interface.

---

## Exemple 1 : Vérification d'espace disque

**Question utilisateur :** "Je veux vérifier l'espace disque disponible sur mon serveur"

**Réponse IA attendue :**

```markdown
## Analyse

Pour vérifier l'espace disque disponible, je vous propose plusieurs options selon le niveau de détail souhaité.

### Commande recommandée

```json
{
  "commands": [
    {
      "cmd": "df -h",
      "risk": "low",
      "description": "Affiche l'espace disque de tous les systèmes de fichiers montés"
    },
    {
      "cmd": "du -sh /*",
      "risk": "low",
      "description": "Affiche la taille de chaque répertoire à la racine"
    }
  ]
}
```

### Explications

- `df -h` : Commande de base, **sans risque**, affiche un résumé
- `du -sh /*` : Plus détaillé mais peut prendre du temps sur de gros systèmes

💡 **Conseil** : Commencez par `df -h` pour avoir une vue d'ensemble.
```

---

## Exemple 2 : Redémarrage d'un service (risque moyen)

**Question utilisateur :** "Le service nginx ne répond plus, je dois le redémarrer"

**Réponse IA attendue :**

```markdown
## Diagnostic : Service nginx

Avant de redémarrer, je recommande de vérifier l'état du service.

### Étape 1 : Vérification

```json
{
  "commands": [
    {
      "cmd": "systemctl status nginx",
      "risk": "low",
      "description": "Vérifie l'état actuel du service nginx"
    },
    {
      "cmd": "nginx -t",
      "risk": "low",
      "description": "Teste la configuration nginx pour détecter les erreurs"
    }
  ]
}
```

### Étape 2 : Redémarrage

⚠️ **Attention** : Cette commande va interrompre temporairement le service web.

```json
{
  "commands": [
    {
      "cmd": "systemctl restart nginx",
      "risk": "medium",
      "description": "Redémarre le service nginx (interruption de service)"
    }
  ]
}
```

### Note importante

Si `nginx -t` montre des erreurs de configuration, **ne redémarrez pas** le service avant de les corriger, sinon nginx ne redémarrera pas.
```

---

## Exemple 3 : Suppression de fichiers (risque élevé)

**Question utilisateur :** "Je veux nettoyer les vieux logs de plus de 30 jours"

**Réponse IA attendue :**

```markdown
## 🚨 Nettoyage de logs - ATTENTION

La suppression de fichiers est une opération irréversible. Je vous recommande de procéder en deux étapes.

### Étape 1 : Vérification (OBLIGATOIRE)

```json
{
  "commands": [
    {
      "cmd": "find /var/log -name '*.log' -mtime +30 -ls",
      "risk": "low",
      "description": "Liste les fichiers .log modifiés il y a plus de 30 jours"
    }
  ]
}
```

### Étape 2 : Suppression

⚠️ **DANGER - IRRÉVERSIBLE** : Vérifiez BIEN la liste ci-dessus avant d'exécuter cette commande !

```json
{
  "commands": [
    {
      "cmd": "find /var/log -name '*.log' -mtime +30 -delete",
      "risk": "high",
      "description": "SUPPRIME DÉFINITIVEMENT les fichiers .log de plus de 30 jours"
    }
  ]
}
```

### Alternatives plus sûres

- Archiver au lieu de supprimer : `tar -czf old_logs.tar.gz ...`
- Utiliser `logrotate` pour une gestion automatisée
- Déplacer vers `/tmp` d'abord pour vérifier

💡 **Conseil** : Ne supprimez jamais de logs sans avoir vérifié la liste au préalable.
```

---

## Bonnes pratiques pour les réponses IA

### Structure recommandée

```markdown
## [Titre de la section]

[Explication du contexte]

### [Sous-section si nécessaire]

```json
{
  "commands": [...]
}
```

[Notes, avertissements, conseils]
```

### Utilisation du Markdown

- **Titres** : `##` pour les sections principales, `###` pour les sous-sections
- **Listes** : `-` pour les listes à puces, `1.` pour les listes numérotées
- **Code inline** : \`backticks\` pour les noms de commandes, fichiers, etc.
- **Gras** : `**texte**` pour mettre en évidence
- **Italique** : `*texte*` pour les notes
- **Emojis** : 💡 (conseil), ⚠️ (attention), 🚨 (danger), ✅ (validé), ❌ (erreur)
- **Blockquotes** : `>` pour les citations ou notes importantes

### Niveaux de risque

- **low** : Commandes de lecture seule, aucun impact sur le système
  - Exemples : `ls`, `cat`, `df`, `ps`, `systemctl status`

- **medium** : Modifications réversibles ou redémarrages de service
  - Exemples : `systemctl restart`, `chmod`, édition de fichiers

- **high** : Suppressions, modifications système critiques, arrêts de service
  - Exemples : `rm -rf`, `dd`, `systemctl stop`, `reboot`, `shutdown`

### Conseils de rédaction

1. **Toujours expliquer** : Donnez du contexte avant de proposer une commande
2. **Plusieurs étapes** : Proposez d'abord la vérification, puis l'action
3. **Avertissements** : Utilisez ⚠️ ou 🚨 pour les risques
4. **Alternatives** : Mentionnez d'autres approches quand pertinent
5. **Pédagogie** : Expliquez ce que fait chaque commande
