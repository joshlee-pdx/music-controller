from datetime import timedelta
from .models import SpotifyToken
from django.utils import timezone
from datetime import timedelta
from .credentials import CLIENT_ID, CLIENT_SECRET
from requests import post, put, get

BASE_URL = "https://api.spotify.com/v1/me/"

# Check and return if user has any existing tokens
def get_user_tokens(session_id):
  # Check if any tokens associated with user
  user_tokens = SpotifyToken.objects.filter(user=session_id)
  if user_tokens.exists(): # If so, return the token
    return user_tokens[0] 
  else:
    return None           

def update_or_create_user_tokens(session_id, access_token, token_type, expires_in, refresh_token):
  tokens = get_user_tokens(session_id)
  expires_in = timezone.now() + timedelta(seconds=expires_in) # Convert expires_in from 3600 seconds into a time stamp 1 hour from now

  # If user has existing token, update it
  if tokens:
    tokens.access_token = access_token
    tokens.refresh_token = refresh_token
    tokens.expires_in = expires_in
    tokens.token_type = token_type
    tokens.save(update_fields=['access_token', 'refresh_token', 'expires_in', 'token_type'])
  # Otherwise, create a token for the user
  else:
    tokens = SpotifyToken(user=session_id, access_token=access_token, refresh_token=refresh_token, token_type=token_type, expires_in=expires_in)
    tokens.save()

def is_spotify_authenticated(session_id):
  # Check if authenticated 
  tokens = get_user_tokens(session_id)
  if tokens: 
    expiry = tokens.expires_in
    if expiry <= timezone.now(): # Refresh token if token is expired
      refresh_spotify_token(session_id)

    return True

  return False

def refresh_spotify_token(session_id):
  refresh_token = get_user_tokens(session_id).refresh_token

  # Post request to spotify to get a new access token and a new refresh token
  response = post('https://accounts.spotify.com/api/token', data={
    'grant_type': 'refresh_token',
    'refresh_token': refresh_token,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET
  }).json()

  access_token = response.get('access_token')
  token_type = response.get('token_type')
  expires_in = response.get('expires_in')

  update_or_create_user_tokens(session_id, access_token,token_type,expires_in,refresh_token)

def execute_spotify_api_request(session_id, endpoint, post_=False, put_=False):
  tokens = get_user_tokens(session_id) # Get token of session host
  headers = {'Content-Type': 'application/json', 'Authorization': "Bearer " + tokens.access_token} # Send authorization token to spotify

  if post_:
    post(BASE_URL + endpoint, headers=headers)
  if put_:
    put(BASE_URL + endpoint, headers=headers)

  response = get(BASE_URL + endpoint, {}, headers=headers)

  try:
    return response.json()
  except:
    return {'Error': 'Issue with request'}

def play_song(session_id):
  return execute_spotify_api_request(session_id, "player/play", put_=True)

def pause_song(session_id):
  return execute_spotify_api_request(session_id, "player/pause", put_=True)