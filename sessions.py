"""Look at the chats Atlas has stored in Firestore, or clear them.

Show them:    python sessions.py
Delete them:  python sessions.py --clear
"""

import argparse

from google.cloud import firestore

options = argparse.ArgumentParser()
options.add_argument("--clear", action="store_true", help="delete every stored chat")
args = options.parse_args()

# Where the Agent Development Kit keeps them:
# adk-session / atlas / users / visitor / sessions / <one document per chat> / events
chats = firestore.Client().collection("adk-session").document("atlas").collection("users").document("visitor").collection("sessions")

found = list(chats.stream())
print(f"{len(found)} chats stored in Firestore")

for chat in found[:5]:
    events = list(chat.reference.collection("events").stream())
    print(f"  {chat.id[:8]}   {len(events)} events")
if len(found) > 5:
    print(f"  ... and {len(found) - 5} more")

if args.clear:
    for chat in found:
        for event in chat.reference.collection("events").stream():
            event.reference.delete()
        chat.reference.delete()
    print("All cleared.")
