from django.db import models
from django.contrib.auth.models import User
import random
from . import exceptions
from observable import Observable
from functools import wraps
from itertools import chain
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType


# Create your models here.


class Card(models.Model):
    """
    Cards that Users can create and play with.
    Users create instances of Cards when they play.
    """

    # Cards are deleted if Users are deleted.
    creator = models.ForeignKey(to=User, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=250)
    cost = models.IntegerField(default=0)
    picture = models.ImageField(upload_to='card_pictures/', null=True)  # User may omit picture

    def __str__(self):
        return self.name

    @property
    def picture_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            return self.picture.url

    class Meta:
        abstract = True


class MonsterCard(Card):
    hp = models.IntegerField(default=1)
    attack = models.IntegerField(default=1)

class SpellCard(Card):
    effect = models.CharField(max_length=500)


class HeroCard(Card):
    hp = models.IntegerField(default=30)
    effect = models.CharField(max_length=500)


# MonsterCard is the card that Monsters are derived from.
# MonsterCard remains the same during play, while Monsters can be created from them and change during play
# class Monster(models.Model):
#     """
#     Monsters are objects with traits based on MonsterCard that exists on a User's field in a GameState.
#     """
#     # Monster card that this Monster originated from
#     card = models.ForeignKey(to=MonsterCard, on_delete=models.CASCADE, default=None)
#     current_hp = models.IntegerField(null=True)
#     current_attack = models.IntegerField(null=True)
#
#     @classmethod
#     def create(cls, card):
#         """ Initializes a Monster based on a MonsterCard """
#         monster = cls(card=card)
#         monster.current_hp = card.hp
#         monster.current_attack = card.attack
#         monster.save()


class Deck(models.Model):
    """
    A list of Cards belonging to a User.
    Users can create Decks.
    Decks are used to create DeckStates for games.
    """
    name = models.CharField(max_length=100, null=True)  # name of the deck
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)  # User that owns this deck
    monster_cards = models.ManyToManyField(MonsterCard, blank=True)
    spell_cards = models.ManyToManyField(SpellCard, blank=True)

    def __str__(self):
        return self.name

    def add_card(self, card):
        """
        Handles the addition of a card to a User's Deck after it has been created.
        :param card:
        :return:
        """
        # add card to correct field
        if isinstance(card, MonsterCard):
            self.monster_cards.add(card)
        elif isinstance(card, SpellCard):
            self.spell_cards.add(card)
        else:
            raise exceptions.InvalidCard
        self.save()


class GameState(models.Model):
    """
    Records the current state of a card game between two Users.
    Handles commands given by Users.
    """

    # Key that users use to access a game
    room_name = models.SlugField()

    # How many turns has it been?
    turn = models.IntegerField(null=True)

    # Has the game started?
    is_started = models.BooleanField(default=False)

    # Has the game been ended?
    is_ended = models.BooleanField(default=False)

    # Winner of the game, if there is one
    winner = models.ForeignKey(to=User, on_delete=models.SET_NULL, default=None, null=True,
                               related_name='winner')

    # Helper methods that initialize the game

    def create_player_states(self):
        """
        Creates PlayerStates that GameState keeps tracks of
        :return:
        """
        self.save()

        player_1_state = PlayerState.objects.create(is_moving=True, is_first=True)
        player_1_state.game_state = self

        player_2_state = PlayerState.objects.create(is_moving=False, is_first=False)
        player_2_state.game_state = self

        player_1_state.save()
        player_2_state.save()


        # self.player_moving_state = PlayerState.objects.create()
        # self.player_1_state = self.player_moving_state
        # self.player_waiting_state = PlayerState.objects.create()
        # self.player_2_state = self.player_waiting_state

    def register(self, user):
        """
        Registers a User as a player in this GameState
        User defines a player and his deck in this GameState
        When valid, we create a PlayerState for GameState to keep track of.
        :param user:
        :return:
        """

        # TODO Check user has preferred deck

        # If playerstate is not available, create a playerstate
        player_1_state = self.player_1_state
        player_2_state = self.player_2_state

        # Two positions are available
        if player_1_state.user is None and player_2_state.user is None:
            if random.randint(0, 1) is 0:
                player_1_state.user = user
            else:
                player_2_state.user = user
        # NOTE: self.player_1 and user are not the same type
        # One position is available
        elif player_1_state.user is None and user != player_2_state.user:
            player_1_state.user = user
        elif player_2_state.user is None and user != player_1_state.user:
            player_2_state.user = user
        else:
            pass  # No position available, do nothing

        player_1_state.save()
        player_2_state.save()

    # User commands

    def start_game(self):
        """
        A game starts.
        :return:
        """
        # Check game already started
        if self.is_started:
            raise exceptions.GameAlreadyStarted

        self.turn = 0
        self.player_moving_state.initialize()
        self.player_waiting_state.initialize()
        self.is_started = True
        self.save()

    def surrender(self):
        pass

    def end_turn(self, user):
        """
        User wants to end his turn.
        :param user: User that wants to end turn
        :return:
        """
        # Reference players
        player_moving_state = self.player_moving_state
        player_waiting_state = self.player_waiting_state

        print(player_moving_state.user, player_waiting_state.user, user)
        # Check authorization
        if user != player_moving_state.user:
            raise exceptions.NotAuthorized

        # Check game started
        if not self.is_started:
            raise exceptions.GameNotStarted

        # Check game ended
        if self.is_ended:
            raise exceptions.GameEnded

        # Players switch moving / waiting
        player_moving_state.is_moving = False
        player_waiting_state.is_moving = True

        # Save to db
        player_moving_state.save()
        player_waiting_state.save()

        # Increment turn counter
        self.turn += 1

        # Field card effects trigger
        player_moving_state.fieldstate.trigger_end_of_turn_effects()
        player_waiting_state.fieldstate.trigger_end_of_turn_effects()

        # Next player draws a card
        self.draw_card(player_waiting_state.user)

        # Next player increments max mana and restores mana
        player_moving_state.max_mana += 1
        player_moving_state.mana = player_moving_state.max_mana

        # Save to db
        player_moving_state.save()
        player_waiting_state.save()
        self.save()

    # Accessors
    @property
    def player_moving_state(self):
        """
        Get the player whose turn it is to move.
        :return:
        """
        return self.playerstate_set.get(is_moving=True)

    @property
    def player_waiting_state(self):
        """
        Get the player whose turn it is to wait.
        :return:
        """
        return self.playerstate_set.get(is_moving=False)

    @property
    def player_1_state(self):
        """
        Gets the player who goes first in the game.
        :return:
        """
        # TODO: The returning object doesn't actually reference it
        return self.playerstate_set.get(is_first=True)

    @property
    def player_2_state(self):
        """
        Gets the player who goes second in the game.
        :return:
        """
        return self.playerstate_set.get(is_first=False)

    # Mutators
    def draw_card(self, user):
        """
        User wants to draw a card.
        :return:
        """
        # Check authorization
        if user != self.player_moving_state.user:
            raise exceptions.NotAuthorized

        # Check game started
        if not self.is_started:
            raise exceptions.GameNotStarted

        # Check game ended
        if self.is_ended:
            raise exceptions.GameEnded

        # Remove a random card from moving player's deck and put it in their hand
        self.player_moving_state.draw_card()

    def summon(self, user, hand_card_position, field_card_position):
        """
        User wants to summon a monster from the hand to the field.
        Hand position and field position is the information necessary to service this command.
        :return:
        """
        # Reference player
        player_moving_state = self.player_moving_state

        # Check authorization
        if user != player_moving_state.user:
            print(user, player_moving_state.user)
            raise exceptions.NotAuthorized

        # Check game started
        if not self.is_started:
            raise exceptions.GameNotStarted

        # Check game ended
        if self.is_ended:
            raise exceptions.GameEnded

        # Reference candidate hand positions
        hand_card = player_moving_state.handstate.handcard_set.get(position=hand_card_position)
        # The hand card must be a monster card
        monster_card = MonsterCardState.objects.get(pk=hand_card.card.pk)

        # If a field card already occupies position, then it is already occupied
        field_cards = player_moving_state.fieldstate.fieldcard_set.filter(position=field_card_position)
        if field_cards.count() is not 0:
            raise exceptions.FieldPositionOccupied

        # Check if enough mana
        cost = hand_card.card.cost
        if cost > player_moving_state.mana:
            raise exceptions.ManaInsuffcient

        # Add field card, remove hand card, and remove the cost in mana
        player_moving_state.fieldstate.add_card(monster_card=monster_card, position=field_card_position)
        player_moving_state.handstate.remove_card(hand_card)

        player_moving_state.mana -= cost
        player_moving_state.save()

        self.save()

    def cast(self, user):
        pass

    def attack(self, user, attacking_field_card_position, defending_field_card_position):
        """
        User wants a monster under his control to fight a monster under his opponent's control.
        :param user:
        :param attacking_field_card_position:
        :param defending_field_card_position:
        :return:
        """
        player_moving_state = self.player_moving_state
        player_waiting_state = self.player_waiting_state

        # Check authorization
        if user != player_moving_state.user:
            raise exceptions.NotAuthorized

        # Check game started
        if not self.is_started:
            raise exceptions.GameNotStarted

        # Check game ended
        if self.is_ended:
            raise exceptions.GameEnded

        # Reference attacking and defending field cards
        attacker = player_moving_state.fieldstate.fieldcard_set.get(position=attacking_field_card_position)
        defender = player_waiting_state.fieldstate.fieldcard_set.get(position=defending_field_card_position)

        # Check immediate attack
        if attacker.turns_alive is 0 and not attacker.charge:
            raise exceptions.AttackOnTurnSummonedWithoutCharge

        # Check attacks left
        if attacker.attacks_left <= 0:
            raise exceptions.AttacksNoneLeft

        # Perform combat
        attacker.hp -= defender.attack
        defender.hp -= attacker.attack
        attacker.attacks_left -= 1

        attacker.save()
        defender.save()

        # If a field card has 0 or less hp, it is removed from the field
        if attacker.hp <= 0:
            player_moving_state.fieldstate.remove_card(attacker)
        if defender.hp <= 0:
            player_waiting_state.fieldstate.remove_card(defender)

    def attack_player(self, user, attacking_field_card_position, defending_player_name):
        player_moving_state = self.player_moving_state
        player_waiting_state = self.player_waiting_state

        # Check authorization
        if user != player_moving_state.user:
            raise exceptions.NotAuthorized

        # Check game started
        if not self.is_started:
            raise exceptions.GameNotStarted

        # Check game ended
        if self.is_ended:
            raise exceptions.GameEnded

        # Reference attacking field card and defending player
        attacker = player_moving_state.fieldstate.fieldcard_set.get(position=attacking_field_card_position)
        defender = player_waiting_state

        # Check defending player is valid
        if defender.user.username != defending_player_name:
            raise exceptions.AttackInvalidPlayer

        # Check immediate attack
        if attacker.turns_alive is 0 and not attacker.charge:
            raise exceptions.AttackOnTurnSummonedWithoutCharge

        # Check attacks left
        if attacker.attacks_left <= 0:
            raise exceptions.AttacksNoneLeft

        # Calculate combat
        attacker.attacks_left -= 1
        defender.hp -= attacker.attack

        # If player has 0 or less hp, then game is over, and is won by attacking player
        if defender.hp <= 0:
            self.is_ended = True
            self.winner = player_moving_state.user

        attacker.save()
        defender.save()
        self.save()

    def delete_game(self):
        """
        Removes the entire game from the database.
        Deletes the GameState and its children PlayerState, DeckState, HandState, FieldState, DeckCard, HandCard,
        FieldCard objects
        :return:
        """

        # Check game started
        if not self.is_started:
            raise exceptions.GameNotStarted

        # TODO Make players dependent on game

        # Delete players
        self.player_moving_state.delete()
        self.player_waiting_state.delete()
        # Delete game
        self.delete()


class PlayerState(models.Model):
    """
    The current state of a registered User in a GameState.
    Contains information unique to a player's stats in a GameState
    """
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, null=True, default=None)

    # game that the player belongs to
    game_state = models.ForeignKey(to=GameState, on_delete=models.CASCADE, null=True, default=None)
    # player can move
    is_moving = models.BooleanField()
    # player goes first or second
    is_first = models.BooleanField()

    hp = models.IntegerField(null=True)
    mana = models.IntegerField(null=True)
    max_mana = models.IntegerField(null=True)

    # deck = models.OneToOneField(to=DeckState, on_delete=models.SET_NULL, null=True)
    # hand = models.OneToOneField(to=HandState, on_delete=models.SET_NULL, null=True)
    # field = models.OneToOneField(to=FieldState, on_delete=models.SET_NULL, null=True)

    def initialize(self):
        """
        Define the starting values of a PlayerState.
        User must be registered first.
        """
        self.hp = 30
        self.mana = 1
        self.max_mana = 1

        # Save DeckInstance into database, and have PlayerState reference it
        preferred_deck = UserSettings.objects.get(user=self.user).preferred_deck  # this user's preferred deck

        DeckState.create(player_state=self, deck=preferred_deck)
        HandState.objects.create(player_state=self)
        FieldState.objects.create(player_state=self)

        self.save()

    def draw_card(self):
        """
        A random card is removed from the player's deck and added to the players's hand.
        :return:
        """
        card = self.deckstate.remove_random_card()
        self.handstate.add_card(card)
        print('Finished drawing card')
        self.save()

    # def lose_hp(self, amount):
    #     """
    #     This player loses hp equal to amount. If all hp is lost, then the game is over.
    #     :param amount:
    #     :return:
    #     """
    #     self.hp -= amount
    #     self.save()


# TODO: Make field, deck and hand cards depend on MonsterCardState instead of MonsterCard


class DeckState(models.Model):
    """
    The current state of a User's deck in a game.
    """
    player_state = models.OneToOneField(to=PlayerState, on_delete=models.CASCADE)
    # deck = models.ForeignKey(to=Deck, on_delete=models.SET_NULL, null=True)

    @classmethod
    def create(cls, player_state, deck):
        """
        Create a DeckState.
        Create MonsterCardState for each MonsterCard needed.
        Create DeckCard for each MonsterCardState.
        Associate DeckCard with corresponding MonsterCardState.
        """
        # Create DeckState
        deck_state = cls(player_state=player_state)  # User defined parameters for the creation of a deck instance
        deck_state.save()
        # TODO: For now, each card has count=1

        # Using MonsterCard, create MonsterCardState. Using MonsterCardState create DeckCard
        for monster_card in deck.monster_cards.all():
            # Create MonsterCardState, a game specific card based on user created card
            monster_card_state = MonsterCardState.create_from_card(card=monster_card, game=player_state.game_state)
            # Create DeckCard, associate it with MonsterCardState, and add it to DeckState
            deck_card = DeckCard.objects.create(content_object=monster_card_state, count=1, deck_state=deck_state)
            # deck_state.deckcard_set.add(deck_card)  # No need to call save after adding
            deck_card.save()

        # for spell_card in deck.spell_cards.all():
        #     spell_card_state = SpellCardState.objects.create(game=player_state.game_state, deck_card=spell_card)
        #     deck_card = DeckCard.objects.create(card=spell_card_state, count=1)
        #     deck_state.deckcard_set.add(deck_card)

        # deck_state.save()
        return deck_state

    def remove_random_card(self):
        """
        Remove a random card from the deck
        :return: Card that was removed
        """
        print('DeckState.remove_random_card()')
        # Check if empty
        num_cards = self.deckcard_set.count()
        if num_cards is 0:
            raise exceptions.DeckEmpty

        # Select a random card from deck
        # TODO: Not random since we're considering
        deck_card_index = random.randint(0, num_cards - 1)
        deck_card = self.deckcard_set.all()[deck_card_index]
        # Remove one card from deck and return card
        # TODO: Always removing the deck card works when each DeckCard has count=1
        card = deck_card.card
        deck_card.delete()
        return card

        # TODO: Make deck_card.card refer to MonsterCardState or SpellCardState


class DeckCard(models.Model):
    """
    Represents the state of a card in a player's deck.
    """
    deck_state = models.ForeignKey(to=DeckState, on_delete=models.CASCADE, null=True)
    count = models.IntegerField()  # Number of copies

    # Generic relation to cards
    content_type = models.ForeignKey(ContentType, models.SET_NULL, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    # Older
    # card = models.ForeignKey(Card, models.SET_NULL, null=True)

    @property
    def card(self):
        return self.content_object

class HandState(models.Model):
    """
    The current state of a player's hand in a game.
    """
    player_state = models.OneToOneField(to=PlayerState, on_delete=models.CASCADE)

    def add_card(self, card):
        """
        Adds a card to this hand.
        :param card: MonsterCardState or SpellCardState
        :return:
        """
        print('HandState.add_card()')

        # TODO: Make compatible with spell
        # Check card type
        if not isinstance(card, MonsterCardState):
            raise exceptions.InvalidCard
        # Check if too many cards to add another card
        if self.handcard_set.count() >= 10:
            raise exceptions.HandFull
        # Check if position is available
        position = self.get_next_position()
        if position is None:
            raise exceptions.HandPositionOccupied

        # Create hand card
        hand_card = HandCard.objects.create(content_object=card, position=position, hand_state=self)
        # self.handcard_set.add(hand_card)  # Associate hand card with

        self.save()

    def remove_card(self, hand_card):
        """
        Removes a card from this hand.
        :param hand_card:
        :return:
        """
        hand_card.delete()
        # self.handcard_set.remove(hand_card)

    def get_next_position(self):
        """
        Returns the next position available in the hand not occupied by another hand card.
        :return:
        """
        position = 0
        while position in map(lambda x: x.position, self.handcard_set.all()):
            position += 1
        if position >= 10:
            position = None
        return position

        # max_position_hand_card = self.handcard_set.all().aggregate(models.Max('position'))
        # return max_position_hand_card.position + 1


class HandCard(models.Model):
    """
    Represents the state of a card in a player's hand.
    """
    hand_state = models.ForeignKey(to=HandState, on_delete=models.CASCADE, null=True)
    position = models.IntegerField()

    # Generic relation to cards
    content_type = models.ForeignKey(ContentType, models.SET_NULL, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    # Older
    # card = models.ForeignKey(Card, models.SET_NULL, null=True)

    @property
    def card(self):
        return self.content_object


class FieldState(models.Model):
    """
    The current state of a player's field in a game.
    """
    player_state = models.OneToOneField(to=PlayerState, on_delete=models.CASCADE)

    def add_card(self, monster_card, position):
        """
        Adds a card to this field.
        :return:
        """
        if not isinstance(monster_card, MonsterCardState):
            raise exceptions.InvalidCard
        # Check if too many cards to add another card
        if self.fieldcard_set.count() >= 7:
            raise exceptions.FieldFull
        # Check if candidate position is occupied by another field card
        if position in map(lambda x: x.position, self.fieldcard_set.all()):
            raise exceptions.FieldPositionOccupied

        # Reference the card this monster card is based on
        # card = MonsterCardState.objects.get(pk=monster_card.pk)

        field_card = FieldCard.objects.create(field_state=self, content_object=monster_card, position=position,
                                              attack=monster_card.attack, hp=monster_card.hp, turns_alive=0,
                                              attacks_per_turn=1, attacks_left=1)
        # Add field card to the field
        # self.fieldcard_set.add(field_card)
        self.save()

    def remove_card(self, field_card):
        """
        Removes a card from this field.
        :param position:
        :return:
        """
        # Reference card to be removed
        # field_card = self.field_cards.filter(position=position)
        field_card.delete()

    def trigger_end_of_turn_effects(self):
        """
        Field card values change from the end of a player's turn.
        :return:
        """
        for field_card in self.fieldcard_set.all():
            field_card.turns_alive += 1
            field_card.attacks_left = field_card.attacks_per_turn
            field_card.save()


class FieldCard(models.Model):
    """
    Represents the state of a card in a player's field.
    """
    field_state = models.ForeignKey(to=FieldState, on_delete=models.CASCADE, null=True)
    position = models.IntegerField(null=True)
    attack = models.IntegerField()
    hp = models.IntegerField()
    turns_alive = models.IntegerField(default=0)
    attacks_per_turn = models.IntegerField(default=1)
    attacks_left = models.IntegerField(null=True)
    charge = models.BooleanField(default=False)

    # Generic relation to cards
    content_type = models.ForeignKey(ContentType, models.SET_NULL, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    # Older
    # card = models.ForeignKey(Card, models.SET_NULL, null=True)

    @property
    def card(self):
        return self.content_object


class MonsterCardState(models.Model):
    """
    A copy of a MonsterCard specific to a Game
    """
    creator = models.ForeignKey(to=User, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=250)
    cost = models.IntegerField(default=0)
    picture = models.ImageField(upload_to='card_pictures/', null=True)  # User may omit picture
    hp = models.IntegerField(default=1)
    attack = models.IntegerField(default=1)

    game = models.ForeignKey(GameState, models.CASCADE)

    # Can be generically related to by
    deck_cards = GenericRelation(DeckCard)
    hand_cards = GenericRelation(HandCard)
    field_cards = GenericRelation(FieldCard)

    @classmethod
    def create_from_card(cls, card, game):
        """
        Create game copy of MonsterCard using MonsterCard. Relate with game.
        Does not associate this object as a deck, hand, or field card.
        :param card: MonsterCard
        :param game: GameState
        :return:
        """
        monster_card_state = cls(creator=card.creator, name=card.name, description=card.description, cost=card.cost,
                                 picture=card.picture, hp=card.hp, attack=card.attack, game=game)
        monster_card_state.save()
        return monster_card_state

    @property
    def picture_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            return self.picture.url

# class SpellCardState(models.Model):
#     """
#     A copy of a SpellCard specific to a Game
#     """
#     game = models.ForeignKey(GameState, models.CASCADE)
#     # Can be generically related to by
#     deck_card = GenericRelation(DeckCard)
#     hand_card = GenericRelation(HandCard)
#     field_card = GenericRelation(FieldCard)


class UserSettings(models.Model):
    """
    Stores information unique to each User for this app.
    """
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    preferred_deck = models.ForeignKey(to=Deck, on_delete=models.PROTECT, null=True)  # Deck User uses in a game
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True)


# TODO: Implement the Observer design pattern that will handle game events

"""
Event Listener: A change in state that the game reports
    - A monster is summoned
    - A spell is played
    - 
    - Card X is summoned
    - Card X is healed
    - Card X is destroyed
    - Card X is returned to hand
    - Card X is targeted by a spell
    - Beginning of Player X's turn
    - End of Player X's turn
    - Beginning of a Player's turn
    - End of a Player's turn
    

Effect: Created by users.
    - Deal X damage to all enemies randomly
    - Deal X damage to an enemy
    - Deal X damage to N random enemies
    - Deal X damage to all field cards
    - Deal X damage to everyone (including players)
    - Deal X damage to 
    
Effects: A list of Effect that change the game. Created by users.
    - Ex: Effects: Deal X damage to an enemy, deal X damage to other player    
    

Event Handler: An object containing an Event and an Effect. When the event occurs, the effect will occur.
    - Ex: (Card X is destroyed, Card X's owner draws 1 card)
        - This Effect is dependent on the Event. This might be bad.
        - We cannot design an Effect like this because it will only make sense with particular events.
        - Instead we should do: (Card X is destroyed, Player 1 draws 1 card)
        
Q: How to create Event Handlers in the game?
A: Users create Event Handlers and assign them to Cards.

Implementing Monster Card Abilities
    - A monster card with an ability is a Card associated with an Event Handler

Implementing Spell Cards
    - A spell card is a card with an event handler of form (Occurs immediately, spell card effect)
    
Thus by implementing Events and Effects, we will have already implemented spell cards

"""
# # Examples (that I should delete eventually)
#
# # TODO Implement Effects
# # Effects are models that Users can create
# # When a user creates a custom effect, such as Player X: destroy N field cards:
#
# obs = Observable()  # Takes in a string specifying event and makes a decorator that will invoke function calls based upon event
#
# # EX: Define function that create effects
# # An effect function being called is equal to it occuring
#
#
# def create_effect_destroy_field_cards(player_pk, num):
#     def destroy_field_cards():
#         """Randomly destroy a certain number of a Player's field cards"""
#         game = GameState
#         player = PlayerState.objects.get(player_pk)
#         return
#     return destroy_field_cards
#
#
# # Create an effect that when invoked: randomly destroys 2 of player with pk 1's field cards
# effect_1 = create_effect_destroy_field_cards(1, 2)
#
# # Create an event handler that when a certain event is detected, will invoke effect_1
# effect_1 = obs.once('event')(effect_1)


# Effects are user created

# class EffectRemoveFieldCards(models.Model):
#     """
#     User created effects that destroy field cards
#     Cannot store anything about a particular gamestate
#     """
#     creator = models.ForeignKey(User, on_delete=models.CASCADE)  # Creator of the effect
#     player = models.CharField()  # player to target
#     num = models.IntegerField()  # number of field cards to remove


# class EffectPlayer(models.Model):
#     """
#     User created effect.
#     Describes how to change a player's stats.
#     """
#     player = models.CharField()  # player to target
#     change_hp_by = models.IntegerField()  # how much to change player's hp
#     change_mana_by = models.IntegerField()  # how much to change player's mana

# TODO: Make an abilities
# class EffectStatePlayer(models.Model):
#     """
#     When invoked, changes a player's stats.
#     """


# class Ability(models.Model):
#     """
#     Contains an event to listen to.
#     """