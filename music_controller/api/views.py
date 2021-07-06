from django.db.models.query import QuerySet
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.serializers import Serializer
from .serializers import RoomSerializer, CreateRoomSerializer, UpdateRoomSerializer
from .models import Room
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse, response

# Allows to view all rooms and create a room
class RoomView(generics.ListAPIView):
  queryset = Room.objects.all()
  serializer_class = RoomSerializer

# Get the room using the room code
class GetRoom(APIView):
  serializer_class = RoomSerializer
  lookup_url_kwarg = 'code'

  def get(self,request, format=None):
    # Find room code by searching a passed in 'code' variable
    code = request.GET.get(self.lookup_url_kwarg)

    if code != None:
      # Get a list of all rooms with the same room code (should be 1)
      room = Room.objects.filter(code=code)
      if len(room) > 0:
        # Grab data from that room
        data = RoomSerializer(room[0]).data
        # Set session key holder to be the host of the room
        data['is_host'] = self.request.session.session_key == room[0].host
        return Response(data,status=status.HTTP_200_OK)
      return Response({'Room Not Found': 'Invalid Room Code.'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'Bad Request': 'Code parameter not found in request'}, status=status.HTTP_400_BAD_REQUEST)

class JoinRoom(APIView):
  lookup_url_kwarg = 'code'

  def post(self,request, format=None):
    # Check if user has a current active session with webserver
    if not self.request.session.exists(self.request.session.session_key):
      self.request.session.create() # If not, create one

    # Get the room code from the request
    code = request.data.get(self.lookup_url_kwarg)
    if code != None:
      # Make a list of all rooms with the same code as requested (should be 1)
      room_result = Room.objects.filter(code=code)
      if len(room_result) > 0: # Found the room
        room = room_result[0]
        self.request.session['room_code'] = code # Store user of current session in this room
        return Response({'message': 'Room Joined!'}, status=status.HTTP_200_OK)
      return Response({'Bad Request': 'Invalid Room Code'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'Bad Request': 'Invalid post data, did not find a code key'}, status=status.HTTP_400_BAD_REQUEST)


# Create rooms
class CreateRoomView(APIView):
  serializer_class = CreateRoomSerializer

  def post(self, request, format=None):
    # Check if user has a current active session with webserver
    if not self.request.session.exists(self.request.session.session_key):
      self.request.session.create() # If not, create one

    # Serialize requested data and check if it is valid
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      # Set room settings to request data
      guest_can_pause = serializer.data.get('guest_can_pause')
      votes_to_skip = serializer.data.get('votes_to_skip')
      host = self.request.session.session_key

      # Check list of rooms to check if host has an active room
      queryset = Room.objects.filter(host=host)
      if queryset.exists(): # If so, just update settings
        room = queryset[0]
        room.guest_can_pause = guest_can_pause
        room.votes_to_skip = votes_to_skip
        room.save(update_fields=['guest_can_pause', 'votes_to_skip'])
        self.request.session['room_code'] = room.code # Store user of current session in this room
        return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
      else: # Otherwise, create room
        room = Room(host=host, guest_can_pause=guest_can_pause,
                    votes_to_skip=votes_to_skip)
        room.save()
        self.request.session['room_code'] = room.code # Store user of current session in this room
        return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)

    return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)

# Send get request to endpoint to check if user is currently in a room, then return the room (in case of events such as disconnects)
class UserInRoom(APIView):
  def get(self,request,format=None):
    # Check if user has a current active session with webserver
    if not self.request.session.exists(self.request.session.session_key):
      self.request.session.create() # If not, create one

    data = {
      'code': self.request.session.get('room_code')
    }
    return JsonResponse(data,status=status.HTTP_200_OK)

class LeaveRoom(APIView):
  def post(self, request, format=None):
    if 'room_code' in self.request.session:
      # Remove room code from user session
      self.request.session.pop('room_code')

      # Check to see if user is host of that room 
      host_id = self.request.session.session_key
      room_results = Room.objects.filter(host=host_id)
    
      # If so, delete that room
      if len(room_results) > 0:
        room = room_results[0]
        room.delete()
    
    return Response({'Message': 'Success'}, status=status.HTTP_200_OK)

class UpdateRoom(APIView):
  serializer_class = UpdateRoomSerializer

  def patch(self, request, format=None):
    # Check if user has a current active session with webserver
    if not self.request.session.exists(self.request.session.session_key):
      self.request.session.create() # If not, create one
    
    # Check to make sure data/room is valid
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      guest_can_pause= serializer.data.get('guest_can_pause')
      votes_to_skip= serializer.data.get('votes_to_skip')
      code= serializer.data.get('code')

      # Check list of rooms to see if room exists
      queryset = Room.objects.filter(code=code)
      if not queryset.exists():
        return Response({'Message': "Room not found."}, status=status.HTTP_404_NOT_FOUND)

      room = queryset[0]

      # Check to make sure that the user submitting changes is the host of the room
      user_id = self.request.session.session_key
      if room.host != user_id:
        return Response({'Message': "You are not the host of this room."}, status=status.HTTP_403_FORBIDDEN)

      # Update room fields/data
      room.guest_can_pause = guest_can_pause
      room.votes_to_skip = votes_to_skip
      room.save(update_fields=['guest_can_pause','votes_to_skip'])
      return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)

    return Response({'Bad Request': 'Inavlid Data...'}, status=status.HTTP_400_BAD_REQUEST)