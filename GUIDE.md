# Speaker guide: 90 minutes

One question for the room, asked at the start and answered by the end:

> It works on your laptop. What happens when a hundred people open it at once?

Attendees have their own handout, `guide/Atlas-Cloud-Run-Guide.pdf`. This page
is the order to present in.

Before the session: open Docker Desktop, run `python check.py`, and build the
image once so the slow package step is cached. Delete any old `atlas` service
and `atlas` image repository so every command runs fresh.

| time | step | the one new idea | what the room sees |
|---|---|---|---|
| 0:00 | the map, running locally | where we start | Atlas answering on a laptop |
| 0:05 | `atlas/app.py` | four small changes, no rewrite | Change 1 to Change 4 |
| 0:12 | `Dockerfile`, `serve.sh`, `docker build` | an image is the app in a box | the build steps |
| 0:22 | `docker run` | the box runs anywhere | the map on localhost:8080, the instance badge |
| 0:30 | Artifact Registry, `docker push` | the cloud needs to fetch the image | layers being pushed |
| 0:38 | `gcloud run deploy` | one command, a URL | Forbidden in the browser, then the proxy |
| 0:48 | logs | the cloud has no terminal | `turn instance=...` lines |
| 0:53 | load test, default settings | one instance takes 20 users | 1 instance, 20 of 20 |
| 1:00 | `--concurrency 4 --max-instances 5` | Cloud Run scales, the app forgets | 3 instances, 6 of 20 |
| 1:10 | `ATLAS_SESSIONS=firestore` | shared state | 3 instances, 20 of 20 |
| 1:18 | `sessions.py`, the Firestore console | where the chats went | 20 chats, 4 events each |
| 1:22 | choosing numbers, cost, clean up | what to take home | the three delete commands |
| 1:27 | questions | | |

## Each step, the same four moves

1. **Predict.** "What will happen this time?" Take two answers from the room.
2. **Show the one change.** One file or one command, nothing else on screen.
3. **Run it.**
4. **Name what changed** in one sentence, and move on.

## Windows to have open

| window | what | from |
|---|---|---|
| terminal 1 | the commands | the start |
| terminal 2 | `gcloud run services proxy atlas --region us-central1 --port 8080` | the deploy |
| browser tab 1 | http://localhost:8080 | `docker run` |
| browser tab 2 | Cloud Run console, the atlas service, Metrics tab | the deploy |
| browser tab 3 | Firestore console | the Firestore step |

## The moment that matters

Before the second load test, ask the room: "Twenty users, three instances.
How many will it remember?" Most say twenty. It remembers about six. Then open
the logs and find one session ID on two different instances.

## Numbers from the test run

| settings | instances | remembered |
|---|---|---|
| default, chats in memory | 1 | 20 of 20 |
| concurrency 4, chats in memory | 3 | 6 of 20 |
| concurrency 4, chats in Firestore | 3 | 20 of 20 |

The first build took about three minutes, the push 72 seconds, the deploy 27
seconds. A load test takes one to two minutes.

## If something goes wrong

| what you see | what to do |
|---|---|
| the load test reports requests "turned away and asked again" | expected during a burst; it is the cold start lesson |
| answers are slow or the logs show `429` | the model is busy; wait a minute, or use `--users 10` |
| a chat row ends "the map service refused" | wait a few seconds and ask again; the load test does not use the map |
| the deploy fails to start | run the image locally with `docker run`; it fails the same way and shows why |
| the venue network blocks the push | deploy with `gcloud run deploy atlas --source .`, which builds in the cloud |
