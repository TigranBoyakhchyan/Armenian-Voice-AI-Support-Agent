import os
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

# find .env in the project root (one folder up from token/)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path=env_path)

api_key    = os.environ.get("LIVEKIT_API_KEY")
api_secret = os.environ.get("LIVEKIT_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: LIVEKIT_API_KEY or LIVEKIT_API_SECRET not found in .env")
    print(f"Looking for .env at: {os.path.abspath(env_path)}")
    exit(1)

print(f"Using key: {api_key}", flush=True)

token = AccessToken(api_key=api_key, api_secret=api_secret)
token.with_grants(VideoGrants(room_join=True, room='test-room'))
token.with_identity('user-1')

print(token.to_jwt())