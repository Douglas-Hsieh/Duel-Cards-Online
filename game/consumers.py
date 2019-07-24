from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
import json
from game.models import GameState
from game import exceptions

class AsyncChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):  # Declares that this routine may be suspended and resumed (coroutine)
        """
        Server response to client connection request.
        :return:
        """
        # Channel joins group associated with room name
        self.room_name = self.scope['url_route']['kwargs']['room_name']  # Get room name from routing
        self.group_name = 'game_chat_' + self.room_name
        self.username = self.scope['user'].username

        self.game = GameState.objects.get(room_name=self.room_name)  # Game associated with room name

        # This channel joins a group associated with room name
        await self.channel_layer.group_add(  # Await the resource that is blocking this operation by doing other things.
            self.group_name,  # group name
            self.channel_name  # channel name
        )

        # Accept connection
        await self.accept()

    async def disconnect(self, close_code):
        """
        Server response to the close of a WebSocket connection.
        :return:
        """
        # print('Websocket disconnected')

        # Channel leaves group associated with room name
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        # Notify group that user has disconnected
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'author': 'Server',
                'message': self.username + ' has disconnected.'
            }
        )

    async def receive(self, text_data):
        """
        Server response to message sent by Client.
        Channel sends message to group.
        :return:
        """
        # Deserialize message
        data = json.loads(text_data)
        message = data['message']

        # Send message to group associated with room name
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'author': self.username,
                'message': message,
            }
        )

    async def chat_message(self, event):
        """
        Server response to message received by group that channel is in.
        Each channel in group affected by event echoes message to client.
        :return:
        """
        # Send message contained in event
        author = event['author']
        message = event['message']
        await self.send(text_data=json.dumps(
            {
                'author': author,
                'message': message,
            }
        ))


class GameConsumer(WebsocketConsumer):
    """
    Responds to players connecting and making commands in the game.
    """
    def connect(self):
        """
        Handles players connecting to the part of the server that will handle user requests associated with the game.
        :return:
        """
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = 'game_game_%s' % self.room_name
        self.game = GameState.objects.get(room_name=self.room_name)
        self.user = self.scope['user']

        # Add the channel associated with the connecting WebSocket to the group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )

        # Accept every client
        self.accept()

        self.update_client()

    def disconnect(self, close_code):
        """
        Server responds to client disconnect
        :return:
        """
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

    # TODO: Instead of receiving a command and making each consumer execute the command and send update to client,
    # TODO: Lets do: The consumer the receives the command executes the command and informs all consumers in the game to render the client
    def receive(self, text_data):
        """
        Server respond to data sent from client
        :return:
        """
        print('receive')
        data = json.loads(text_data)

        command = data['command']

        if command == 'start_game':
            self.start_game()
            # print('start_game')
            # self.game.start_game()
        elif command == 'end_turn':
            self.end_turn()
            # self.game.end_turn(self.user)
        elif command == 'delete_game':
            self.delete_game()
            # self.game.delete_game()
        elif command == 'summon':
            self.summon(data)
        elif command == 'attack':
            self.attack(data)
        elif command == 'attack_player':
            self.attack_player(data)


        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'update_client'
                # 'type': data['type']
            }
        )

    # Server response based on type of event

    def update_client(self, event=None):
        """
        Server sends to client the current state of the game.
        Eventually, we should update
        :return:
        """
        print('update_client')

        # If game hasn't started, do not give any information
        if not self.game.is_started:
            return

        self.game.refresh_from_db()
        # TODO: Send different information based on who the User is (player 1 and player 2)

        player_1 = self.game.player_1_state.user
        player_2 = self.game.player_2_state.user

        if self.game.winner:
            winner = self.game.winner.username
        else:
            winner = None

        # Public information
        data = {
            'is_started': self.game.is_started,
            'turn': self.game.turn,
            'winner': winner,

            'player_1_hp': self.game.player_1_state.hp,
            'player_2_hp': self.game.player_2_state.hp,
            'player_1_mana': self.game.player_1_state.mana,
            'player_2_mana': self.game.player_2_state.mana,
            'player_1_max_mana': self.game.player_1_state.max_mana,
            'player_2_max_mana': self.game.player_2_state.max_mana,

            # We cannot reference the deck until we create the deck by initializing player states
            'player_1_deck_counter': self.game.player_1_state.deckstate.deckcard_set.count(),
            'player_2_deck_counter': self.game.player_2_state.deckstate.deckcard_set.count(),
        }
        for index, field_card in enumerate(self.game.player_1_state.fieldstate.fieldcard_set.order_by('position')):
            data['player_1_field_card_' + str(index) + '_position'] = field_card.position
            data['player_1_field_card_' + str(index) + '_name'] = field_card.card.name
            data['player_1_field_card_' + str(index) + '_description'] = field_card.card.description
            data['player_1_field_card_' + str(index) + '_cost'] = field_card.card.cost
            data['player_1_field_card_' + str(index) + '_picture'] = field_card.card.picture_url

            data['player_1_field_card_' + str(index) + '_attack'] = field_card.attack
            data['player_1_field_card_' + str(index) + '_hp'] = field_card.hp
        for index, field_card in enumerate(self.game.player_2_state.fieldstate.fieldcard_set.order_by('position')):
            data['player_2_field_card_' + str(index) + '_position'] = field_card.position
            data['player_2_field_card_' + str(index) + '_name'] = field_card.card.name
            data['player_2_field_card_' + str(index) + '_description'] = field_card.card.description
            data['player_2_field_card_' + str(index) + '_cost'] = field_card.card.cost
            data['player_2_field_card_' + str(index) + '_picture'] = field_card.card.picture_url

            data['player_2_field_card_' + str(index) + '_attack'] = field_card.attack
            data['player_2_field_card_' + str(index) + '_hp'] = field_card.hp

        # Private information
        if self.user.username == player_1.username:
            player_state = self.game.player_1_state
        else:
            player_state = self.game.player_2_state

        for index, hand_card in enumerate(player_state.handstate.handcard_set.order_by('position')):
            data['hand_card_' + str(index) + '_position'] = hand_card.position
            data['hand_card_' + str(index) + '_name'] = hand_card.card.name
            data['hand_card_' + str(index) + '_description'] = hand_card.card.description
            data['hand_card_' + str(index) + '_cost'] = hand_card.card.cost
            data['hand_card_' + str(index) + '_picture'] = hand_card.card.picture_url

        # Send serialized message to client
        message = json.dumps(data)
        self.send(text_data=message)

    def start_game(self):
        """
        Starts the game
        :return:
        """
        print('start_game')
        self.game.start_game()

    def end_turn(self):
        """
        Server handles Player ending his turn
        :return:
        """
        print('end_turn')
        self.game.end_turn(self.user)

        # try:
        #     self.game.end_turn(self.user)
        # except exceptions.NotAuthorized:  # If the user isn't authorized to end turn and tries to do it, ignore it
        #     pass

    def delete_game(self):
        """
        Server handles deleting the game.
        :return:
        """
        print('delete_game')
        self.game.delete_game()

    def surrender(self):
        """
        Server handles the Player resigning
        :param event:
        :return:
        """
        print('surrender')

    def summon(self, data):
        """
        Server handles the Player summoning a card from hand to field.
        :param data:
        :return:
        """
        print('summon')

        # Extract data from message
        hand_card_position = data['handCardPosition']
        field_card_position = data['fieldCardPosition']

        # Summon
        self.game.summon(self.user, hand_card_position, field_card_position)

    def attack(self, data):
        """
        Server handles the Player initiating an attack from one field card onto another.
        :param data:
        :return:
        """
        print('attack')

        # Store data from client
        attacking_field_card_position = data['attackingFieldCardPosition']
        defending_field_card_position = data['defendingFieldCardPosition']

        # Attack
        self.game.attack(self.user, attacking_field_card_position, defending_field_card_position)

    def attack_player(self, data):
        """
        Server handles the Player initiating an attack from one field card to Player
        :param data:
        :return:
        """
        print('attack_player')

        attacking_field_card_position = data['attackingFieldCardPosition']
        defending_player_name = data['defendingPlayerName']

        self.game.attack_player(self.user, attacking_field_card_position, defending_player_name)

