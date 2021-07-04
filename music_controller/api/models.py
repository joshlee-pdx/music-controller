from django.db import models
import string
import random


def generate_unique_code():
  length = 6

  while True:
    code = ''.join(random.choices(string.ascii_uppercase, k=length)) # generate random code that is K length that only contains uppercase ascii characters
    # Get list of all Room objects with their code matching this code, if none are found return this code
    if Room.objects.filter(code=code).count() == 0:
      break
    
  return code

# Create your models here.
class Room(models.Model):
  code = models.CharField(max_length=8, default=generate_unique_code, unique=True)
  host = models.CharField(max_length=50, unique=True)
  guest_can_pause = models.BooleanField(null=False, default=False) # By setting null=False we require a selection
  votes_to_skip = models.IntegerField(null=False, default=1)
  created_at = models.DateTimeField(auto_now_add=True) # Automatically add the date and time room was created
