# Copilot Shell - Description du projet

## 1. Objectif du projet

Créer un **copilote shell interactif** pour l'administration Linux, permettant de proposer des commandes en langage naturel et de les exécuter uniquement après validation humaine. Le projet n'est pas lié spécifiquement à Proxmox, mais il peut être utilisé sur des serveurs hébergeant des VM ou containers.

### Objectifs clés

* Permettre à un utilisateur de poser une question ou de décrire un problème en langage naturel.
* L'IA propose des commandes pertinentes, accompagnées d'une explication et d'un niveau de risque.
* L'utilisateur valide la commande avant exécution.
* Les résultats stdout/stderr sont renvoyés à l'IA comme contexte pour les prochaines propositions.
* L'architecture doit permettre de changer facilement le moteur IA (ChatGPT, Claude, etc.) sans modifier l'UI ou le backend.
* L'utilisateur peut ajouter des profils que l'utilisateur peut gérer. Par exemple passer en mode création de container pour Proxmox.
* La partie Prompt doit gérer une liste de mot de passe sans les connaitre et la partie commande doit être capable de remplacer la clef par la valeur pour execution.

## 2. Contrainte de sécurité

* **Aucune commande ne peut être exécutée automatiquement par l'IA.**
* L'utilisateur doit valider chaque action par entrée même aprés que la commande ai été copié dans la partie SSH.
* Les commandes sont accompagnées d'un niveau de risque et d'une description pour aider la décision.
* Historique complet des commandes et résultats conservé pour audit et contexte.

## 3. Architecture générale

### 3.1 Frontend

* Interface web split :

  * Panneau gauche : IA / chat / propositions de commandes.
  * Panneau droit : terminal affichant stdout/stderr.
* Les commandes proposées par l'IA sont affichées sous forme de boutons cliquables avec description et niveau de risque.
* Les résultats d'exécution sont affichés dans le terminal et ajoutés au contexte pour l'IA.

### 3.2 Backend (Python)

* Framework : FastAPI
* Modules principaux :

  * `AIProvider` : interface abstraite pour tout moteur IA.
  * `ShellExecutor` : exécute les commandes locales (extension SSH possible).
  * `ContextStore` : stocke les commandes et résultats pour l’IA.
* Endpoints REST :

  * `/ai/suggest` : reçoit le message utilisateur, renvoie les propositions de l'IA.
  * `/execute` : exécute la commande validée par l'utilisateur.

### 3.3 IA / moteur de suggestion

* L’IA reçoit le contexte complet des commandes précédentes.
* L'IA ne répond qu'au format Markdown pour avoir une mise en page cohérente coté chat.
* Quand l'IA fait de propositions commande à pousser dans le terminal elle le fait en formatant avec une balise script [```options  formated json ``` et en formatant un json structuré **propositions de commandes au format JSON structuré**.
* Si la commande contient un risque la mise en page le met en évidence dans l'affichage
* 

* Format JSON imposé :

  * `explanation` : texte expliquant l'analyse.
  * `commands` : liste de commandes, chaque commande contient `cmd`, `risk`, `description`.
  * `notes` : texte optionnel.
* Permet d’interchanger facilement le moteur IA (ChatGPT, Claude, LLM local).

## 4. Flux de fonctionnement

1. L’utilisateur envoie un problème ou question en langage naturel.
2. Le backend transmet le message et le contexte à l’IA.
3. L’IA renvoie un JSON structuré avec explications et commandes proposées.
4. L’UI affiche ces commandes sous forme de boutons cliquables.
5. L’utilisateur clique sur une commande pour l’exécuter.
6. `ShellExecutor` exécute la commande et renvoie stdout/stderr.
7. Les résultats sont ajoutés au contexte pour la prochaine interaction avec l’IA.
8. L’utilisateur peut continuer la boucle de diagnostic.

## 5. Contraintes techniques

* Langage : Python (prototype rapide, extensible et compatible avec conteneurs).
* Possibilité de dockeriser le projet.
* Indépendance du backend et de l’UI vis-à-vis du moteur IA.
* Historique des commandes et des résultats conservé pour audit et contexte.
* Extension future possible pour :

  * SSH / exécution distante
  * Whitelist / blacklist des commandes
  * Multi-utilisateur / authentification
  * Terminal interactif complet avec xterm.js

## 6. Extensions futures

* Brancher Claude ou un autre moteur IA via la même interface `AIProvider`.
* Ajouter un `SSHExecutor` pour exécuter des commandes sur des VMs ou containers distants.
* Sécurisation et sandboxing des commandes exécutées.
* Gestion de profils pour différents types de diagnostics (sysadmin, docker, proxmox, rescue Linux).
* Interface terminal plus complète (xterm.js) et meilleure gestion des erreurs.
* gestion des mots de passe

## 7. Philosophie générale

* **Copilote = suggestion, pas exécution automatique.**
* Tout est **validé par l’utilisateur**.
* L’IA est un moteur de suggestion, pas un cerveau décisionnel.
* Le projet vise un équilibre entre **ergonomie**, **sécurité**, et **flexibilité du moteur IA**.

---

Ce document `description.md` synthétise toutes nos discussions et sert de guide pour continuer le projet dans VSCode.
