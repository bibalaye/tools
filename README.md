# 🛠️ DevKit Pro

**DevKit Pro** est un outil tout-en-un conçu spécifiquement pour les développeurs, regroupant les utilitaires les plus fréquents dans une interface graphique (GUI) moderne, rapide et simple d'utilisation.

Fini les multiples onglets de navigateur ouverts pour tester une API, formater un JSON ou nettoyer un CSV. Tout est centralisé dans une application de bureau légère, construite avec **Python et Tkinter**.

---

## ✨ Fonctionnalités

### 🌐 1. API Tester
Un client HTTP léger pour tester vos endpoints d'API REST.
- Support des méthodes `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.
- Gestion des **Headers** personnalisés.
- Support de l'**Authentification** (Bearer Token, Basic Auth, API Key).
- Éditeur de corps de requête (Body JSON).
- Affichage coloré du statut, temps de réponse et taille de la réponse.
- Historique des requêtes avec rechargement rapide.

### 📊 2. CSV Cleaner
Un visualiseur et nettoyeur de fichiers CSV.
- Chargement de gros fichiers CSV de manière optimisée.
- Filtrage rapide et barre de recherche globale.
- Tri ascendant/descendant par colonne.
- **Suppression des doublons** en un clic.
- Export et sauvegarde des fichiers nettoyés.

### 💡 3. JSON Formatter
Un utilitaire pour valider, formater et minifier du JSON.
- **Beautify** : formater avec 2 ou 4 espaces pour la lisibilité.
- **Minify** : condenser le JSON pour réduire sa taille.
- **Validation** et gestion des erreurs de syntaxe indiquant précisément où se trouve l'erreur.
- Actionnement croisé (Envoyer la sortie vers l'entrée).

---

## 🚀 Installation

### Prérequis
- Python 3.6 ou supérieur.
- Le seul paquet externe nécessaire est `requests` pour le module API Tester.

### Étapes

1. Clonez ce dépôt ou téléchargez le fichier source.
2. (Optionnel mais recommandé) Créez un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```
3. Installez les dépendances :
   ```bash
   pip install requests
   ```

---

## 💻 Utilisation

Pour lancer l'application, exécutez simplement le script principal :

```bash
python devkit_pro.py
```

L'interface se lance immédiatement. Vous pouvez naviguer entre les différents outils en utilisant les onglets situés en haut de la fenêtre.

---

## 🎨 Design et Ergonomie

L'interface a été refondue pour offrir une expérience "Pro" aux développeurs :
- **Thème sombre par défaut** (inspiré des IDE modernes type VS Code / IntelliJ) pour réduire la fatigue oculaire.
- **Typographie lisible** : Combinaison de polices monospaces (`Courier New`) pour le code et sans-serif (`Segoe UI`) pour l'interface.
- **Composants plats (Flat Design)** avec retours visuels au survol (hover) pour une interaction fluide.

---
*DevKit Pro - Développé avec ❤️ pour la productivité des devs.*
