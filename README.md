# Racket Stringing App — Docker Deployment

## Prerequisites
- Docker and Docker Compose installed on the target machine
- Git

## 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

## 2. Build and run
```bash
docker compose up -d --build
```

The app will be available at **http://localhost:8501** (or `http://<server-ip>:8501` if deployed on a remote host).

## 3. Data persistence
The SQLite database (`stringing.db`) is stored in a named Docker volume (`app-data`), mounted at `/app/data` inside the container. This means:
- Your data survives `docker compose down` / `docker compose up` and image rebuilds.
- To inspect or back up the volume directly:
  ```bash
  docker run --rm -v <project-folder-name>_app-data:/data -v "$PWD":/backup alpine \
    cp /data/stringing.db /backup/stringing.db
  ```
- You can also just use the in-app **Import / Backup → Download Backup ZIP** button.

## 4. Updating after a `git pull`
```bash
git pull
docker compose up -d --build
```
Your data is untouched since it lives in the separate `app-data` volume, not in the image.

## 5. Stopping
```bash
docker compose down
```
(Add `-v` only if you intentionally want to delete the data volume too — this is destructive.)

## Useful commands
```bash
docker compose logs -f          # tail app logs
docker compose restart          # restart the container
docker compose ps               # check container status
```

## Notes
- `logo.png` / `favicon.png` are optional — if present in the repo root, they'll be used for branding; if absent, the app falls back to a default emoji favicon and skips the sidebar logo.
- Legacy `jobs.csv` / `customers.csv` / `strings.csv` files are auto-migrated into SQLite on first run if found in the data directory — but for a fresh Docker deployment there typically won't be any, so the app just starts with an empty database.
- Want a different host port? Edit the `ports:` line in `docker-compose.yml`, e.g. `"8080:8501"`.
