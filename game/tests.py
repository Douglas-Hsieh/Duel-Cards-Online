from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

# Create your tests here.

class CardTests(TestCase):

    def test_create_one_card(self):
        """
        If a User creates a card, it will be successfully saved.
        :return:
        """
        # Create User
        user = create_user(username='username', password='password')
        # Create Card


def create_user(username='username', password='password'):
    user = User.objects.create(username=username)
    user.set_password(password)
    user.save()
    return user
