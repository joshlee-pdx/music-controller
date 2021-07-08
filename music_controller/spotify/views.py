from django.shortcuts import redirect, render
from .credentials import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET 
from rest_framework.views import APIView
from requests import Request, post
from rest_framework import status
from rest_framework.response import Response
from .util import *
from api.models import Room

# API endpoint that will return URL to authenticate spotify application
class AuthURL(APIView):
  def get(self,request,format=None):
    scopes = 'user-read-playback-state user-modify-playback-state user-read-currently-playing'

    # Prepare a URL that will authenticate spotify application
    url = Request('GET', 'https://accounts.spotify.com/authorize', params={
      'scope': scopes,
      'response_type': 'code',
      'redirect_uri': REDIRECT_URI,
      'client_id': CLIENT_ID,
    }).prepare().url

    return Response({'url':url}, status=status.HTTP_200_OK)

# Callback function to handle retrieved url and gather token information
def spotify_callback(request,format=None):
  code = request.GET.get('code')
  error = request.GET.get('error')

  # Post to spotify and convert it to json
  response = post('https://accounts.spotify.com/api/token', data={
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': REDIRECT_URI,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
  }).json()

  # Gather token information from the response
  access_token = response.get('access_token')
  token_type = response.get('token_type')
  refresh_token = response.get('refresh_token')
  expires_in = response.get('expires_in')
  error = response.get('error')

  # Create a session key for user if they do not have one
  if not request.session.exists(request.session.session_key):
    request.session.create()

  update_or_create_user_tokens(request.session.session_key,access_token,token_type,expires_in,refresh_token)

  # Redirect back to the frontend of our app
  return redirect('frontend:')

class IsAuthenticated(APIView):
  def get(self, request,format=None):
    is_authenticated = is_spotify_authenticated(self.request.session.session_key)
    return Response({'status': is_authenticated}, status=status.HTTP_200_OK)

class CurrentSong(APIView):
  def get(self,request,format=None):
    # Get room code
    room_code = self.request.session.get('room_code')
    room = Room.objects.filter(code=room_code)
    if room.exists(): 
      room = room[0]
    else: # Return if no room exists
      return Response({},status=status.HTTP_404_NOT_FOUND)

    # Get room host because they are the authenticated user that has the song info
    host = room.host

    endpoint = "player/currently-playing"
    response = execute_spotify_api_request(host,endpoint)

    # Error or no song currently playing
    if 'error' in response or 'item' not in response:
      return Response({}, status=status.HTTP_204_NO_CONTENT)

    # Get song info
    item = response.get('item')
    duration = item.get('duration_ms')
    progress = response.get('progress_ms')
    album_cover = item.get('album').get('images')[0].get('url')
    is_playing = response.get('is_playing')
    song_id = item.get('id')

    # Create string of artists in case there are more than 1 artists on a song
    artist_string = ""
    for i, artist in enumerate(item.get('artists')):
      if i > 0:
        artist_string += ", "
      name = artist.get('name')
      artist_string += name

    # Song object to send to frontend
    song = {
      'title': item.get('name'),
      'artist': artist_string,
      'duration': duration,
      'time': progress,
      'image_url': album_cover,
      'is_playing': is_playing,
      'votes': 0,
      'id': song_id
    }

    return Response(song, status=status.HTTP_200_OK)

# Connect the Pause icon button to pausing the actual song
class PauseSong(APIView):
  def put(self,response, format=None):
    # Check to see if user has permission to pause by checking room permissions
    room_code = self.request.session.get('room_code')
    room = Room.objects.filter(code=room_code)[0]
    if self.request.session.session_key == room.host or room.guest_can_pause:
      pause_song(room.host)
      return Response({}, status=status.HTTP_204_NO_CONTENT)
    
    return Response({}, status=status.HTTP_403_FORBIDDEN)

# Connect the play icon button to play the actual song
class PlaySong(APIView):
  def put(self,response, format=None):
    # Check to see if user has permission to pause by checking room permissions
    room_code = self.request.session.get('room_code')
    room = Room.objects.filter(code=room_code)[0]
    if self.request.session.session_key == room.host or room.guest_can_pause:
      play_song(room.host)
      return Response({}, status=status.HTTP_204_NO_CONTENT)
    
    return Response({}, status=status.HTTP_403_FORBIDDEN)