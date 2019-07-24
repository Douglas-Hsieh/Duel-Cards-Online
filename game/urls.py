"""
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
"""

from django.urls import path
from .views import home_view, public_card_list_view, private_card_list_view, card_search_view, card_query_view,\
    deck_list_view, deck_detail_view, DeckCreateView,\
    MonsterCardCreateView, monster_card_update_view,\
    spell_card_create_view, monster_card_detail_view, spell_card_detail_view, \
    deck_add_monster_card_view, \
    room_list_view, room_view, host_view, \
    register_view, \
    user_settings_view

app_name = 'game'  # URL namespace for this app
urlpatterns = [
    path('', home_view, name='home'),

    # MonsterCard
    path('create_monster_card/', MonsterCardCreateView.as_view(), name='create_monster_card'),
    path('<int:pk>/monster_card_update/', monster_card_update_view, name='monster_card_update'),

    path('spell_card_create/', spell_card_create_view, name='spell_card_create'),

    path('<int:pk>/monster_card_detail/', monster_card_detail_view, name='monster_card_detail'),
    path('<int:pk>/spell_card_detail/', spell_card_detail_view, name='spell_card_detail'),

    path('public_card_list/', public_card_list_view, name='public_card_list'),
    path('private_card_list/', private_card_list_view, name='private_card_list'),
    path('card_search/', card_search_view, name='card_search'),
    path('card_query', card_query_view, name='card_query'),

    # Deck
    path('deck_create/', DeckCreateView.as_view(), name='deck_create'),
    path('deck_list/', deck_list_view, name='deck_list'),
    path('<int:pk>/deck_detail/', deck_detail_view, name='deck_detail'),
    path('deck_add_monster_card/', deck_add_monster_card_view, name='deck_add_monster_card'),

    # GameState
    path('host/', host_view, name='host'),
    path('register/', register_view, name='register'),
    path('room_list/', room_list_view, name='room_list'),
    # TODO: <slug> potentially dangerous
    path('room/<slug:room_name>/', room_view, name='room'),

    # UserSettings
    path('user_settings/', user_settings_view, name='user_settings'),
]
