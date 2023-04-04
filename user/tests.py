from django.test import TestCase, Client
from user.models import User
import hashlib
from django.contrib.auth.hashers import make_password, check_password
# Create your tests here.
