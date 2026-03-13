#!/usr/bin/env bash
# =============================================================================
# Script de provisionnement VPS — CTI Platform
# Usage: bash setup-vps.sh [domaine] [email_certbot]
# Exemple: bash setup-vps.sh cti.example.com admin@example.com
# =============================================================================
set -euo pipefail

DOMAIN="${1:-cti.example.com}"
EMAIL="${2:-admin@example.com}"
INSTALL_DIR="/opt/cti-platform"

echo "======================================="
echo "  Installation CTI Platform"
echo "  Domaine : $DOMAIN"
echo "  Répertoire : $INSTALL_DIR"
echo "======================================="

# --- 1. Mise à jour système ---
apt-get update && apt-get upgrade -y

# --- 2. Installation Docker ---
if ! command -v docker &>/dev/null; then
    echo "[*] Installation de Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# --- 3. Installation Docker Compose plugin ---
if ! docker compose version &>/dev/null 2>&1; then
    echo "[*] Installation de Docker Compose..."
    apt-get install -y docker-compose-plugin
fi

# --- 4. Création du répertoire ---
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# --- 5. Copie des fichiers de déploiement ---
cp "$(dirname "$0")/docker-compose.prod.yml" ./docker-compose.yml
# Remplacer le domaine dans la config nginx
sed "s/cti.example.com/$DOMAIN/g" "$(dirname "$0")/nginx.conf" > ./nginx.conf

# --- 6. Fichier .env (à remplir manuellement) ---
if [ ! -f .env ]; then
    cat > .env <<EOF
DATABASE_URL=sqlite:///./cti.db
VIRUSTOTAL_API_KEY=
ABUSEIPDB_API_KEY=
SHODAN_API_KEY=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ALERT_EMAIL_TO=
SLACK_WEBHOOK_URL=
DOCKERHUB_USERNAME=votre_username
EOF
    echo ""
    echo "⚠️  IMPORTANT: Éditez /opt/cti-platform/.env avec vos clés API avant de continuer."
    echo "   nano /opt/cti-platform/.env"
    echo ""
fi

# --- 7. Certificat SSL Let's Encrypt (si domaine valide) ---
if [ "$DOMAIN" != "cti.example.com" ]; then
    echo "[*] Obtention du certificat SSL pour $DOMAIN..."
    docker run --rm \
        -v /etc/letsencrypt:/etc/letsencrypt \
        -v /var/www/certbot:/var/www/certbot \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --agree-tos \
        --no-eff-email \
        --email "$EMAIL" \
        -d "$DOMAIN"
fi

# --- 8. Démarrage ---
echo "[*] Démarrage de la plateforme..."
docker compose pull
docker compose up -d

echo ""
echo "✅ CTI Platform déployée !"
echo "   URL: https://$DOMAIN"
echo "   Docs: https://$DOMAIN/docs"
echo "   Health: https://$DOMAIN/health"
echo ""
echo "Commandes utiles:"
echo "  Logs      : docker compose logs -f cti-api"
echo "  Restart   : docker compose restart cti-api"
echo "  Stop      : docker compose down"
