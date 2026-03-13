# CTI Platform

Plateforme de **Cyber Threat Intelligence** open source construite avec FastAPI et SQLAlchemy.

[![CI](https://github.com/VOTRE_USERNAME/VOTRE_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/VOTRE_USERNAME/VOTRE_REPO/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| **Collecte d'IoCs** | IP, domaines, URLs, hash de fichiers, emails, CVEs |
| **Enrichissement automatique** | VirusTotal, AbuseIPDB, Shodan |
| **Score de risque** | Score 0-100 calculé automatiquement à partir des sources |
| **MITRE ATT&CK** | Corrélation automatique aux techniques ATT&CK |
| **Alertes** | Création auto + notifications Email & Slack |
| **Rapports** | Export JSON, CSV, PDF |
| **Dashboard** | Statistiques et top IoCs risqués |
| **Import en masse** | Endpoint bulk pour importer des listes d'IoCs |

## Démarrage rapide (développement local)

### Prérequis

- Python 3.12+ ou Docker

### 1. Cloner le dépôt

```bash
git clone https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
cd VOTRE_REPO/cti_platform
```

### 2. Configurer l'environnement

```bash
cp .env.example .env
nano .env   # Remplir les clés API
```

### 3a. Lancer avec Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3b. Lancer avec Docker

```bash
docker-compose up -d
```

### 4. Accéder à l'API

| URL | Description |
|---|---|
| http://localhost:8000 | Health check |
| http://localhost:8000/docs | Documentation interactive (Swagger UI) |
| http://localhost:8000/redoc | Documentation ReDoc |
| http://localhost:8000/api/v1/dashboard/stats | Statistiques globales |

---

## Déploiement en production (VPS + CI/CD)

### Prérequis

- Serveur Ubuntu 22.04+ avec IP publique
- Nom de domaine pointant vers votre serveur
- Compte Docker Hub (gratuit)

### Étape 1 — Secrets GitHub Actions

Dans **Settings → Secrets and variables → Actions** de votre dépôt :

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Votre username Docker Hub |
| `DOCKERHUB_TOKEN` | Token Docker Hub (Account → Security → New Access Token) |
| `VPS_HOST` | IP publique ou domaine du serveur |
| `VPS_USER` | Utilisateur SSH (ex: `ubuntu`) |
| `VPS_SSH_KEY` | Contenu complet de `~/.ssh/id_rsa` (clé privée) |

### Étape 2 — Installation initiale sur le VPS

```bash
# Depuis votre machine locale
ssh ubuntu@VOTRE_IP

# Sur le serveur
git clone https://github.com/VOTRE_USERNAME/VOTRE_REPO.git /tmp/cti-repo
bash /tmp/cti-repo/cti_platform/deploy/setup-vps.sh votre-domaine.com admin@email.com

# Configurer les clés API
nano /opt/cti-platform/.env
docker compose -f /opt/cti-platform/docker-compose.yml restart
```

Le script installe Docker, configure **Nginx** comme reverse proxy, obtient un certificat **SSL Let's Encrypt** et démarre la plateforme.

### Étape 3 — Déploiements suivants (automatiques)

Chaque `git push` sur `master` déclenche le pipeline CI/CD :

```
push master
    ├── [CI] Lint (Ruff) + Tests
    ├── [CI] Build image Docker
    ├── [Deploy] Push image → Docker Hub
    └── [Deploy] SSH VPS → docker pull + restart
```

---

## Architecture

```
app/
├── main.py                     # Point d'entrée FastAPI
├── core/
│   ├── config.py               # Configuration (pydantic-settings)
│   └── database.py             # SQLAlchemy engine & session
├── models/
│   ├── ioc.py                  # Modèles IoC et TTP
│   ├── alert.py                # Modèle Alert
│   └── report.py               # Modèle Report
├── schemas/
│   ├── ioc.py                  # Schémas Pydantic IoC/TTP
│   ├── alert.py                # Schémas Pydantic Alert
│   └── report.py               # Schémas Pydantic Report
├── api/routes/
│   ├── iocs.py                 # CRUD IoCs + enrichissement
│   ├── alerts.py               # CRUD Alertes
│   ├── reports.py              # Génération et téléchargement rapports
│   ├── ttps.py                 # Gestion TTPs MITRE ATT&CK
│   └── dashboard.py            # Statistiques globales
└── services/
    ├── enrichment/
    │   ├── virustotal.py       # Enrichissement VirusTotal
    │   ├── abuseipdb.py        # Enrichissement AbuseIPDB
    │   └── shodan.py           # Enrichissement Shodan
    ├── enrichment_manager.py   # Orchestrateur + calcul du score
    ├── correlation.py          # Moteur de corrélation ATT&CK
    ├── alerting.py             # Alertes + notifications
    └── reporting.py            # Génération de rapports
```

## Score de risque

| Score | Niveau | Déclencheur alerte |
|---|---|---|
| 75–100 | CRITICAL | Oui |
| 50–74 | HIGH | Oui |
| 25–49 | MEDIUM | Non |
| 1–24 | LOW | Non |
| 0 | UNKNOWN | Non |

Calculé à partir de : malicious/suspicious VirusTotal, abuse score AbuseIPDB, CVEs Shodan, usage Tor, réputation négative.

---

## Exemples d'utilisation

### Ajouter un IoC

```bash
curl -X POST http://localhost:8000/api/v1/iocs/ \
  -H "Content-Type: application/json" \
  -d '{"value": "1.2.3.4", "ioc_type": "ip", "source": "OSINT", "tags": "botnet,c2"}'
```

### Import en masse

```bash
curl -X POST http://localhost:8000/api/v1/iocs/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "iocs": [
      {"value": "evil.com", "ioc_type": "domain"},
      {"value": "d41d8cd98f00b204e9800998ecf8427e", "ioc_type": "file_hash"}
    ]
  }'
```

### Déclencher un enrichissement manuel

```bash
curl -X POST http://localhost:8000/api/v1/iocs/1/enrich
```

### Générer un rapport PDF

```bash
# Créer le rapport
curl -X POST http://localhost:8000/api/v1/reports/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Rapport hebdomadaire", "format": "pdf", "filters": {"risk_level": "high"}}'

# Télécharger (quand status = "ready")
curl -O http://localhost:8000/api/v1/reports/1/download
```

### Dashboard stats

```bash
curl http://localhost:8000/api/v1/dashboard/stats
```

### Lier un IoC à une technique MITRE ATT&CK

```bash
curl -X POST http://localhost:8000/api/v1/ttps/T1566/iocs/1
```

## Clés API requises

| Service | Variable | Obtention |
|---|---|---|
| VirusTotal | `VIRUSTOTAL_API_KEY` | https://www.virustotal.com/gui/my-apikey |
| AbuseIPDB | `ABUSEIPDB_API_KEY` | https://www.abuseipdb.com/account/api |
| Shodan | `SHODAN_API_KEY` | https://account.shodan.io/ |

> Les enrichissements sont désactivés si les clés API ne sont pas configurées.

## License

MIT
