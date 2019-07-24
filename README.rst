=====
Duel Cards Online
=====

Duel Cards Online is a game inspired by trading card games like Hearthstone that allows users to create and play with customized cards.

Prerequisites
-----------
This app requires you to have django.contrib.auth (to allow site users to register and login as players), Django-Channels (to use WebSockets and Redis that allow for full-duplex communication), django-storages (as a storage backend for user media such as profile pictures and card pictures).

Installation
-----------
After you have installed the prerequisites and configured them correctly in your project settings, you are now ready to install and configure the Duel Cards Online app.

1. Add "game" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'game',
    ]

2. Include the game URLconf in your project urls.py like this::

    path('game/', include('game.urls')),

3. Configure the project routing.py for game like this::

	application = ProtocolTypeRouter({
	    'websocket': AuthMiddlewareStack(
	        URLRouter(
	     		... +
	            game.routing.websocket_urlpatterns
	        )
	    ),
	})

4. Run `python manage.py migrate` to create the game models.

5. Start the development server and visit http://127.0.0.1:8000/game/
   to play the game (note that you need to be a logged in user via Django-Auth to be able to use the app)
