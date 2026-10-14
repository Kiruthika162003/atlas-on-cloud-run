# Atlas on Cloud Run

From demo to production: take an agent that works on a laptop and run it on
Cloud Run without rewriting it. Put it in a container, push the image, deploy
it privately, load-test it, watch instances start under traffic, and move the
chat history to Firestore so it survives across instances.

The agent is Atlas, a map agent built with the Google Agent Development Kit.
It finds three places near you, describes each one from checked sources, and
draws the walk. It was built in
[atlas-agents-workshop](https://github.com/Kiruthika162003/atlas-agents-workshop);
you do not need that repository to follow this one.

New to Docker or Google Cloud? Follow the
[attendee guide](guide/Atlas-Cloud-Run-Guide.pdf). It starts from an empty
laptop: installing Docker, creating a project, switching on each service, and
every step below with real output.

```
                          Cloud Run service "atlas" (private)
                    ┌──────────────────────────────────────────────┐
your browser ─────> │ instance 1   web app + agent + places server │ ──> Gemini (Vertex AI)
load test    ─────> │ instance 2   web app + agent + places server │ ──> Firestore (the chats)
                    │ instance 3   ...started when traffic grows   │ ──> Cloud Logging
                    └──────────────────────────────────────────────┘
```

## What is here

| file or folder | what it is |
|---|---|
| `atlas/` | the web app and the recommendation agent |
| `mcp_server/` | the places server: three map tools over MCP |
| `description_agent/` | a second agent, reached over A2A |
| `skills/` | the walking tour skill |
| `Dockerfile`, `serve.sh` | the container: one image, three processes |
| `loadtest.py` | many users at once, from your laptop |
| `sessions.py` | show or clear the chats stored in Firestore |
| `check.py` | tests your setup and says what to fix |

`atlas/app.py` has four changes that make the app ready for Cloud Run, each
marked with a comment: chats can live in Firestore, every reply names the
instance that sent it, the port comes from `PORT`, and each turn prints one
log line.

## One-time setup

You need Python 3.11 or newer, Git, the Google Cloud CLI, Docker Desktop, and
a Google Cloud project with billing on.

```
gcloud services enable run.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com aiplatform.googleapis.com
```

```
gcloud firestore databases create --location=us-central1
```

```
python -m venv .venv
```

```
.venv\Scripts\activate
```

```
pip install -r requirements-laptop.txt
```

```
copy .env.example .env
```

On macOS and Linux the activate line is `source .venv/bin/activate` and the
copy is `cp .env.example .env`. Put your Project ID in `.env`, then:

```
python check.py
```

## The steps

Replace `YOUR_PROJECT_ID` and `YOUR_SERVICE_URL` with your own.

**1. Build the image**

```
docker build -t atlas .
```

**2. Run it on your laptop** (Windows PowerShell; on macOS and Linux the path is `$HOME/.config/gcloud/application_default_credentials.json`)

```
docker run --rm --name atlas-local -p 8080:8080 --env-file .env -e GOOGLE_APPLICATION_CREDENTIALS=/adc.json -v "$env:APPDATA\gcloud\application_default_credentials.json:/adc.json:ro" atlas
```

Open http://localhost:8080.

**3. Push it to Artifact Registry**

```
gcloud artifacts repositories create atlas --repository-format=docker --location=us-central1
```

```
gcloud auth configure-docker us-central1-docker.pkg.dev
```

```
docker tag atlas us-central1-docker.pkg.dev/YOUR_PROJECT_ID/atlas/atlas:v1
```

```
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/atlas/atlas:v1
```

**4. Deploy it, private**

```
gcloud run deploy atlas --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/atlas/atlas:v1 --region us-central1 --no-allow-unauthenticated --memory 1Gi --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

```
gcloud run services proxy atlas --region us-central1 --port 8080
```

**5. Read the logs**

```
gcloud run services logs read atlas --region us-central1 --limit 12 --log-filter "textPayload:turn" --freshness 30m
```

**6. Twenty users at once**

```
python loadtest.py YOUR_SERVICE_URL --users 20
```

**7. Lower concurrency, and run the load test again**

```
gcloud run services update atlas --region us-central1 --concurrency 4 --max-instances 5
```

**8. Keep chats in Firestore, and run the load test again**

```
gcloud run services update atlas --region us-central1 --update-env-vars ATLAS_SESSIONS=firestore
```

```
python sessions.py
```

## What the load test showed

Twenty users, each saying "Hi, my name is ..." and then "What is my name?".

| settings | instances | remembered |
|---|---|---|
| default (concurrency 80), chats in memory | 1 | 20 of 20 |
| concurrency 4, chats in memory | 3 | 6 of 20 |
| concurrency 4, chats in Firestore | 3 | 20 of 20 |

With chats in memory, each instance only knows the conversations it served
itself. Once Cloud Run spreads a chat across instances, the app forgets
people. Firestore is shared by all of them.

## Clean up

```
python sessions.py --clear
```

```
gcloud run services delete atlas --region us-central1
```

```
gcloud artifacts repositories delete atlas --location us-central1
```

## Good to know

- A burst on a cold service can be turned away with HTTP 429 or 500 while new
  instances start. The load test waits and asks again, and reports how often.
- `serve.sh` runs gunicorn with 16 threads. Keep the Cloud Run concurrency at
  or below that.
- Places and routes come from free OpenStreetMap services that ask for light
  use. Fine for a workshop, not for production.
- On a Mac with an M-series chip, build with `--platform linux/amd64`.
