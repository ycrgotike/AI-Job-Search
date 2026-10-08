# /serverstart - Start AI Job Search Dashboard Server

Launch or verify the interactive AI Job Search radar and matching dashboard on `http://localhost:8000`.

## Purpose
Start the local Python HTTP server (`server.py` via `./app 8000`), serving the interactive opportunity radar, fit score filters, live scraper triggers, and application tracking UI.

## Execution Steps

1. **Check Existing Process:**
   - Inspect port 8000 using `lsof -ti:8000` or process list.
   - If a server process is already running on port 8000, verify responsiveness via `http://localhost:8000/api/stats`.

2. **Launch Server:**
   - If port 8000 is free, launch the server in the background:
     ```bash
     ./app 8000
     ```
   - If another port is requested by the user as an argument (e.g. `/serverstart 8080`), launch with that port instead.

3. **Verify & Respond:**
   - Confirm the server is healthy.
   - Return the active link to the user: **[http://localhost:8000](http://localhost:8000)** (or the selected port).
