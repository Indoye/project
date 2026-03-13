# CTI Platform

Plateforme de **Cyber Threat Intelligence** open source construite avec FastAPI et SQLAlchemy.

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

## Démarrage rapide

### 1. Configurer l'environnement

```bash
cd cti_platform
cp .env.example .env
# Éditer .env avec vos clés API
```

### 2. Lancer avec Docker

```bash
docker-compose up -d
```

### 3. Lancer en local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Accéder à l'API

- **Documentation interactive**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

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

### Générer un rapport

```bash
curl -X POST http://localhost:8000/api/v1/reports/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Rapport hebdomadaire", "format": "json", "filters": {"risk_level": "high"}}'
```

### Dashboard stats

```bash
curl http://localhost:8000/api/v1/dashboard/stats
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
