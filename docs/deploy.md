# Deployment guide for Ric AI web app

This document provides a simple deployment flow to run Ric AI behind Nginx and secure it with Let's Encrypt. It assumes you own `ricai.com` (or a domain you control).

Overview
- The web app runs in Docker (see `web/Dockerfile`) and listens on port 8000
- Nginx handles TLS termination and can be used as a reverse proxy to the web container

Quick Docker compose (local)
1. Build and run:

   docker-compose up --build

2. Visit http://localhost:8000 to access the web app.

Production with Nginx and Let's Encrypt
1. Provision a host (VM) and install Docker and Docker Compose.
2. Create an Nginx config to proxy `ricai.com` to the Docker container on port 8000.
3. Use certbot to obtain and manage certificates. Example Nginx snippet:

   server {
     listen 80;
     server_name ricai.com www.ricai.com;
     location / {
       proxy_pass http://127.0.0.1:8000/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
     }
   }

4. Use certbot to get certs and configure nginx to serve https.

Notes
- For production, ensure you run the app in a dedicated Python venv or container and monitor resource usage.
- If you plan to enable online transformer mode on the server, pre-download models (see `scripts/predownload_model.py`) and provide sufficient RAM/disk.
- For a production-ready deployment consider adding authentication, rate-limiting, logging, and monitoring.
