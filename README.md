# DanceSyncWeb

Simple frontend + backend for extracting and syncing audio from dance videos.

## Backend (Flask)

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   # install ffmpeg separately (e.g. `brew install ffmpeg` on macOS)
   ```

2. Run locally:
   ```bash
   python app.py          # uses PORT=10000 by default
   ```

   Or build the Docker image and start with port environment variable:
   ```bash
   docker build -t dancesync-backend backend
   docker run -p 10000:10000 dancesync-backend
   ```

3. Health check available at `/` and sync endpoint at `/sync` (also `/upload` for
  legacy video uploads).  CORS is enabled so the frontend can call from another
  origin.  You can also open `backend/test.html` once the server is running to
  manually POST files from the server itself.

## Frontend

The frontend is just a static HTML/JS page (`index.html`).

- Open the file directly in your browser, or serve it from a simple HTTP server:
  ```bash
  # you can use Python's built-in server:
  cd /path/to/DanceSyncWeb
  python -m http.server 8000  # then visit http://localhost:8000/index.html
  ```

- or if you prefer npm, a `package.json` is provided so that `npm run serve`
  will launch `http-server` on port 8000.

- The page will attempt to contact the backend at the same origin (i.e.
  `window.location.origin`).  If you host the frontend separately, set the
  constant in the script accordingly.

- Click **Sync Audio** after selecting a video and the page will extract audio
  locally via `ffmpeg.wasm` and POST to `/sync`.

## Deployment notes

- The backend uses the `PORT` environment variable and supports running under
  gunicorn (see `gunicorn_conf.py`).  Render or other hosts will set this for
  you.
- For free tiers that sleep on inactivity, an external monitor or cron job is
  needed; the in-process `keep_alive()` thread is only helpful for local
  development.

---

Feel free to extend the `/sync` handler with real song recognition or
Audio/Video processing!
