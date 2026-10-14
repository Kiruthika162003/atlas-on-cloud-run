"""Check your setup, one thing at a time. It stops at the first problem and says how to fix it.

Run: python check.py
"""

import os
import shutil
import subprocess
import sys


def ok(what):
    print(f"  [ ok ]  {what}")


def stop(what, fix):
    print(f"  [ FIX ] {what}\n          {fix}")
    sys.exit(1)


def run(command):
    """Run a command and hand back whether it worked and what it printed."""
    done = subprocess.run(command, shell=True, capture_output=True, text=True)
    return done.returncode == 0, done.stdout.strip()


print("\nChecking your setup\n")

# 1. Python itself
version = f"{sys.version_info.major}.{sys.version_info.minor}"
if sys.version_info < (3, 11):
    stop(f"Python {version} is too old.", "Install Python 3.11 or newer from python.org/downloads.")
ok(f"Python {version}")

# 2. The two packages the laptop scripts use
try:
    import requests  # noqa: F401
    from google.cloud import firestore
except ImportError as missing:
    stop(f"A package is missing: {missing.name}.",
         "Switch on the virtual environment, then run: pip install -r requirements-laptop.txt")
ok("The packages are installed")

# 3. The settings file
here = os.path.dirname(os.path.abspath(__file__))
project = ""
if os.path.exists(os.path.join(here, ".env")):
    for line in open(os.path.join(here, ".env")):
        if line.startswith("GOOGLE_CLOUD_PROJECT="):
            project = line.split("=", 1)[1].strip()
if not project or project == "your-project-id":
    stop("There is no .env file with your project in it.",
         "Copy .env.example to .env and set GOOGLE_CLOUD_PROJECT to your Project ID.")
ok(f"The settings file points at project {project}")

# 4. Docker, installed and running
if not shutil.which("docker"):
    stop("The docker command was not found.", "Install Docker Desktop, then close this terminal and open a new one.")
if not run("docker info")[0]:
    stop("Docker is installed but not running.", "Open Docker Desktop and wait until it says the engine is running.")
ok("Docker is running")

# 5. The Google Cloud command line tool, signed in and pointed at the same project
if not shutil.which("gcloud"):
    stop("The gcloud command was not found.",
         "Install the Google Cloud CLI, then close this terminal and open a new one.")
account = run("gcloud config get-value account")[1]
if not account or account == "(unset)":
    stop("gcloud is not signed in.", "Run: gcloud auth login")
if run("gcloud config get-value project")[1] != project:
    stop("gcloud is pointed at a different project than .env.", f"Run: gcloud config set project {project}")
ok(f"gcloud is signed in as {account}")

# 6. The sign-in that programs use
import google.auth
from google.auth.exceptions import DefaultCredentialsError

try:
    google.auth.default()
except DefaultCredentialsError:
    stop("Programs on this computer are not signed in to Google Cloud.",
         "Run: gcloud auth application-default login")
ok("Programs on this computer are signed in")

# 7. The four services this session uses
NEEDED = {
    "run.googleapis.com": "Cloud Run",
    "artifactregistry.googleapis.com": "Artifact Registry",
    "firestore.googleapis.com": "Firestore",
    "aiplatform.googleapis.com": "Vertex AI",
}
enabled = run('gcloud services list --enabled --format="value(config.name)"')[1].split()
for service, name in NEEDED.items():
    if service not in enabled:
        stop(f"{name} is not switched on for this project.", f"Run: gcloud services enable {service}")
ok("Cloud Run, Artifact Registry, Firestore and Vertex AI are switched on")

# 8. A Firestore database to keep the chats in
try:
    list(firestore.Client(project=project).collection("adk-session").limit(1).stream())
except Exception:
    stop("This project has no Firestore database yet.", "Run: gcloud firestore databases create --location=us-central1")
ok("The Firestore database answers")

print("\nEverything works. You are ready to build the container.\n")
