# Friday

Friday provides the environment and model-call layers for a future desktop-operating AI agent. It starts an Ubuntu XFCE desktop in Docker, exposes the desktop in a browser, provides a local authenticated HTTP API for screenshots and mouse and keyboard input, and can ask a vision model to locate a point. It does not yet run an agent loop or click anything from a model result.

```
Host Python app / RemoteExecutor -- HTTP --> control server -- X11Backend --> X display
          |                                      |
          +-- browser --> Webtop viewer ----------+
```

## Prerequisites

- Python 3.11 or newer
- Docker Engine running and accessible to your user

## Quickstart

```sh
pip install -e '.[dev]'
python -m friday up
```

The `up` command prints a browser viewer URL and a control API URL. Stop and remove the container when finished:

```sh
python -m friday down
```

## CLI

```sh
python -m friday up
python -m friday status
python -m friday screenshot out.png
python -m friday act '{"action":"left_click","x":100,"y":100}'
python -m friday act '{"action":"screenshot"}' --screenshot out.png
python -m friday locate "open the terminal" --image s.png --annotate result.png
python -m friday down
```

The first command writes an ignored `.friday-state.json` in the current directory so later CLI commands can use the running sandbox's generated token. Run these commands from the same directory.

Host code receives a `Sandbox` and never needs to know whether it is backed by Docker:

```python
from friday.desktop.client import DesktopClient
from friday.executor import RemoteExecutor
from friday.actions import parse_action
from friday.sandbox.docker_sandbox import DockerSandbox

with DockerSandbox() as sandbox, DesktopClient(sandbox) as desktop:
    executor = RemoteExecutor(desktop)
    executor.execute(parse_action('{"action":"left_click","x":100,"y":100}'))
```

## Project structure

```
docker/       Custom Webtop image and s6 service
server/       FastAPI control service run inside the container
src/friday/   Host-side configuration, sandbox abstraction, client, and CLI
src/friday/llm/  Provider-neutral vision LLM interface and Featherless adapter
src/friday/graph/  Small LangGraph coordinate-location workflow
src/friday/vision/  Coordinate conversion and screenshot annotation
tests/        Unit and opt-in integration tests
```

## Control API

`GET /health` is unauthenticated. All other endpoints require `Authorization: Bearer <per-run token>`:

- `GET /screenshot` returns PNG bytes.
- `GET /screen_size` returns the current display dimensions.
- `GET /cursor` returns the current cursor point.
- `POST /action` accepts one validated typed desktop action.

Actions are a shared Pydantic discriminated union on `action`: clicks, drag, move,
mouse down/up, scroll, type, key, held key, wait, screenshot, cursor position, and
host-only zoom. Coordinates are integer X11 pixels. Server failures return a clear
HTTP error including command stderr; client failures raise `DesktopError` subclasses.

`RemoteExecutor` sends server actions via `DesktopClient`. `zoom` is deliberately
host-only: it crops and enlarges a PNG using Pillow and returns `ZoomView`, whose
`to_screen(x, y)` maps a zoomed-image point back to a real display pixel.

## Lifecycle and display settings

`DockerSandbox` uses the official Docker Python SDK. It builds `friday-webtop:local` when that image is missing (or when rebuild is requested), binds the viewer and API to `127.0.0.1`, and creates a fresh random control token for each new sandbox. If a container with the configured name already exists, Friday force-removes it and starts a replacement; this avoids attaching a new token to an old service. `down` force-removes the named container.

Current LinuxServer Selkies documentation identifies Webtop's HTTP viewer as container port `3000` (with HTTPS at `3001`). Friday maps the requested HTTP viewer port. The image supports Wayland, but Friday sets `PIXELFLUX_WAYLAND=false` so the base image starts its documented Xvfb `DISPLAY=:1` path, which is required by `xdotool` and `scrot`.

Friday sets `SELKIES_MANUAL_WIDTH` and `SELKIES_MANUAL_HEIGHT` from `FridayConfig` (defaults: 1280×720). The current Selkies configuration reference says either value enables manual-resolution mode and disables browser-driven resizing. `screen_size` reports what X11 actually uses, so clients can check coordinates before acting.

## Security

Friday binds both the viewer and control API to `127.0.0.1` only. It creates a new random API token for every run. The API has full control of the desktop; treat it like a remote shell and do not expose either port to an untrusted network.

## LLM layer

Friday's graph depends only on the `VisionLLM` interface:

```python
def invoke(prompt: str, images: list[bytes]) -> LLMResponse: ...
```

The included Featherless adapter is the only provider. It uses `langchain_openai.ChatOpenAI` against Featherless's OpenAI-compatible endpoint. PNGs are encoded as `data:image/png;base64,...` URLs in the request; no image is uploaded to a public URL. The model returns plain text, and Friday strictly parses JSON rather than using provider tool-calling or structured-output features.

Configure it by copying the example and setting values locally:

```sh
cp .env.example .env
# Set FEATHERLESS_API_KEY and FRIDAY_LLM_MODEL in .env
```

`FEATHERLESS_API_KEY` and `FRIDAY_LLM_MODEL` are required. `FRIDAY_LLM_MODEL` has no hardcoded default so deployment selects a Featherless vision-capable Qwen model explicitly. `.env` is ignored by Git. Never commit or log an API key.

Run location against a saved screenshot or the active sandbox:

```sh
python -m friday locate "open the terminal" --image s.png --annotate located.png
python -m friday locate "open the terminal" --live
```

The model is asked for integer `(x, y)` values on a configurable normalized grid (default `0..1000`). Friday reads the actual dimensions from the exact PNG sent to the model and converts with `round(value / grid * size)`, clamped to the final valid pixel. This keeps model coordinates independent of image size while making returned pixel values usable by callers later.

To add a provider, create one class implementing `VisionLLM` under `src/friday/llm/providers/`, then add its name and class to `PROVIDERS` in `registry.py`. Nothing outside `friday.llm` needs to import that provider's SDK.

## Known issues

Docker access is required for the live desktop. On hosts where the Docker socket is not available to the current user, image build, container start, and the opt-in integration test cannot run.

The Featherless model must support vision. Verify the selected model in Featherless's model catalog before using `--image` or `--live`; a text-only Qwen model cannot process screenshots. Model output is probabilistic, so callers should inspect the printed coordinate or `--annotate` image before using it for any desktop action.

## Development

```sh
make build
make test
make lint
RUN_INTEGRATION=1 pytest -m integration
RUN_LLM_INTEGRATION=1 pytest -m integration tests/test_llm_integration.py
```

The Docker integration test is marked and skipped unless `RUN_INTEGRATION=1` is set. It builds or uses the local image, starts Docker, and verifies an actual PNG and X11 display size. The Featherless integration test is marked and skipped unless `RUN_LLM_INTEGRATION=1` is set; it makes one text and one vision request.

## Decisions

- Docker is isolated behind the `Sandbox` interface so agent code depends only on `Sandbox` and `DesktopClient`.
- The control service runs as an s6-managed process inside the image instead of via `docker exec`.
- The Docker SDK manages lifecycle; the Docker CLI is only used by the developer `Makefile` build target.
- Vision coordinates are normalized before conversion so different screenshot resolutions use one model-facing convention.
- Plain-text JSON parsing is used because it works across the documented Featherless vision API without requiring model-specific structured-output support.
