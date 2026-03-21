from livekit.api import AccessToken, VideoGrants

token = AccessToken(api_key='devkey', api_secret='secret')
token.with_grants(VideoGrants(room_join=True, room='test-room'))
token.with_identity('user-1')
print(token.to_jwt())