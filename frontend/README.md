# Friday UI

Standalone React + Vite interface. All UI code, dependencies, build settings,
and assets stay in this directory and are separate from the Python application
and Docker control-server image.

## Start Friday

Start the existing desktop sandbox from the repository root:

```sh
python -m friday up
```

The CLI prints the local Webtop viewer URL and API URL. Put those URLs in
`frontend/.env.local` (the ports can change each time Friday starts):

```dotenv
VITE_VIEWER_URL=http://127.0.0.1:<viewer-port>
VITE_BACKEND_URL=http://127.0.0.1:<api-port>
```

Then start the UI from `frontend/`:

```sh
npm install
npm run dev -- --open
```

Vite opens the UI in the default browser. The page embeds the existing
Webtop/Selkies desktop; it does not start a second sandbox. Stop the desktop
from the repository root with `python -m friday down`.

The backend URL is used by Vite's development proxy for only the unauthenticated
`GET /health` route. No desktop token or LLM key is read by the frontend. The
current API's screenshot, screen-size, and action routes require a bearer token,
so the browser does not call them.

## Current integration limits

The Python API has no task submission/status/history, task event stream,
pause/resume/cancel, or manual-control coordination interface. The UI makes
those limits explicit, leaves execution controls disabled, and does not
simulate task progress. Users can still operate Ubuntu directly in the viewer.
Resolution is not displayed because the existing screen-size route is
authenticated with the private desktop token.

## Frontend checks

```sh
npm test
npm run build
npm run lint
```
