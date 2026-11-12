# Site vitrine de RudyLink Infrastructure (point 02)
<!-- onglet: Site vitrine -->

Site statique : trois pages HTML, une feuille de style, aucun JavaScript ni outil de build. Il se modifie directement dans les fichiers.

| Fichier | Contenu |
|---|---|
| `index.html` | La société, ses services, le projet en cours, l'équipe, le contact |
| `projet.html` | Le projet IUT, premiers résultats, documents, calendrier |
| `journal.html` | Journal de bord (ajouter chaque entrée en haut de la liste) |
| `assets/style.css` | Mise en forme (couleurs et polices de la charte, RLI-COM-001) |
| `documents/` | Copies des PDF livrés, mises à jour par `python3 communication/build.py` |

## Hébergement sur l'architecture du projet

Le site est un service de la **DMZ** du site de Marseille :

```
Internet ──▶ EL-FGT1/2 (FortiGate) ──▶ DM-RP1/2 (Caddy, HTTPS) ──▶ DM-WEB1 (nginx, fichiers statiques)
```

- **DM-WEB1** sert les fichiers. Si l'option de virtualisation de la DMZ est retenue (voir le point 14), c'est un conteneur LXC Debian sur le cluster Proxmox **NM-PVE1/2/3**, avec la haute disponibilité Proxmox. Sinon, c'est le serveur physique prévu au chiffrage.
- **DM-RP1/2** porte le certificat TLS et le nom public. Les deux reverse proxies assurent la redondance.
- Le FortiGate n'ouvre vers la DMZ que les ports 80 et 443, et seulement vers les reverse proxies.

### DM-WEB1 : nginx

```bash
apt install nginx
rsync -a --delete livrables/site_web/ admin@dm-web1:/var/www/rudylink/
```

`/etc/nginx/sites-available/rudylink` :

```nginx
server {
    listen 80;
    server_name infra.rudylink.eu;
    root /var/www/rudylink;
    index index.html;

    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header Referrer-Policy strict-origin-when-cross-origin;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ /README\.md$ {
        deny all;
    }
}
```

### DM-RP1 et DM-RP2 : Caddy

```caddy
infra.rudylink.eu {
    reverse_proxy dm-web1:80
    encode gzip
    header Strict-Transport-Security "max-age=31536000"
}
```

Le nom `infra.rudylink.eu` est une proposition. Dans la maquette, il peut être remplacé par un nom interne (`www.rudylink.lan`, par exemple) servi par le DNS de la DMZ (DM-DNS1).
