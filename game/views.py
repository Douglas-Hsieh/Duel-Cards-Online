from django.shortcuts import render, redirect, reverse
from django.views.generic import ListView, CreateView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from game.models import Card
from game.models import MonsterCard, SpellCard, GameState, Deck, UserSettings
from game.forms import MonsterCardForm, SpellCardForm, DeckForm, GameStateForm, UserSettingsForm


from django.http import JsonResponse

from django.contrib import messages

# Create your views here.


@login_required
def home_view(request):
    """
    Homepage
    :param request:
    :return:
    """
    context = {}
    return render(request, 'game/home.html', context)


# Card Views

class MonsterCardCreateView(LoginRequiredMixin, CreateView):
    model = MonsterCard  # Specifies the model fields
    form_class = MonsterCardForm  # Specifies the mapping between model fields and form fields
    template_name = 'game/card_create.html'  # Template used as user form interface
    success_url = '/game/create_monster_card'  # Corresponds to a path to follow after successful form submission

    # Called when valid form data is POSTed. Returns an HttpResponse.
    # Override (redefine) form_valid which does the form saving and redirect.
    def form_valid(self, form):
        creator = self.request.user
        obj = form.save(commit=False)
        obj.creator = creator
        obj.save()
        return render(self.request, 'game/home.html')


@login_required
def monster_card_update_view(request, pk):
    """
    Handles display or update of a MonsterCard
    """
    print('monster_card_update_view')
    # Reference Monster card selected
    try:
        card = MonsterCard.objects.get(pk=pk)
    except MonsterCard.DoesNotExist:
        messages.add_message(request, messages.ERROR, 'Monster card does not exist.')
        return redirect(to=reverse('game:home'))

    print(card)

    # Check authorized
    if card.creator == request.user.username:
        messages.add_message(request, messages.ERROR, 'Unauthorized to edit this card.')
        return redirect(to=reverse('game:home'))

    # Handle depending on type of request
    if request.POST:
        print('post')
        form = MonsterCardForm(request.POST, request.FILES)
        if form.is_valid():
            # Update monster card
            card.name = form.cleaned_data['name']
            card.description = form.cleaned_data['description']
            card.cost = form.cleaned_data['cost']
            # Delete old picture, save new picture
            card.picture.delete()
            card.picture = form.cleaned_data['picture']
            card.hp = form.cleaned_data['hp']
            card.attack = form.cleaned_data['attack']

            card.save()
    else:
        print('get')
        form = MonsterCardForm(instance=card)

    context = {'form': form}
    return render(request, 'game/card_create.html', context)

# @login_required
# def create_monster_card_view(request):
#     """
#     Users can create a Monster Card.
#     :param request:
#     :return:
#     """
#     # User chooses type of card to create
#
#     # Format the data the user submitted as a MonsterCardForm.
#     form = MonsterCardForm(request.POST or None)
#     created_card_name = None
#
#     if form.is_valid():
#         # Process information on the form.
#         form.save()
#         created_card_name = form.cleaned_data['name']
#         # Empty the form.
#         form = MonsterCardForm()
#
#     context = {
#         'form': form,
#         'created_card_name': created_card_name,
#     }
#
#     # Direct user to form page, using form as information the form page template
#     return render(request, 'game/create_card.html', context)

@login_required
def spell_card_create_view(request):
    """
    Creates Spell Cards associated with an User
    :param request:
    :return:
    """
    form = SpellCardForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            obj = form.save(commit=False)
            obj.creator = request.user
            obj.save()
            form = SpellCardForm()
        else:
            form = SpellCardForm()

    context = {
        'form': form
    }
    return render(request, 'game/card_create.html', context)


@login_required
def monster_card_detail_view(request, pk):
    """
    Displays a monster card's details to the user
    :param request:
    :param pk: id of card
    :return:
    """
    try:
        monster_card = MonsterCard.objects.get(pk=pk)
    except MonsterCard.DoesNotExist:
        messages.add_message(request, messages.ERROR, 'Attempt to view monster card details failed.')
        return redirect(to=reverse('game:home'))
    decks = Deck.objects.filter(user=request.user)
    context = {
        'card': monster_card,
        'decks': decks,
    }
    return render(request, 'game/card_detail.html', context)


@login_required
def spell_card_detail_view(request, pk):
    """
    Displays a spell card's details to the user
    :param request:
    :param pk:
    :return:
    """
    try:
        spell_card = SpellCard.objects.get(pk=pk)
    except SpellCard.DoesNotExist:
        messages.add_message(request, messages.ERROR, 'Attempt to view monster card details failed.')
        return redirect(to=reverse('game:home'))
    decks = Deck.objects.filter(user=request.user)
    context = {
        'card': spell_card,
        'decks': decks,
    }
    return render(request, 'game/card_detail.html', context)


@login_required
def public_card_list_view(request):
    """
    Lists the public's Cards.
    :return: 
    """
    context = {
        'monsters': MonsterCard.objects.all(),
        'spells': SpellCard.objects.all(),
        'decks': Deck.objects.filter(user=request.user)
    }
    return render(request, 'game/card_list.html', context)


@login_required
def private_card_list_view(request):
    """
    Lists the User's Cards.
    :return:
    """
    context = {
        'monsters': MonsterCard.objects.filter(creator=request.user),
        'spells': SpellCard.objects.filter(creator=request.user),
    }
    return render(request, 'game/card_list.html', context)


def card_search_view(request):
    """
    Search page
    :param request:
    :return:
    """
    return render(request, 'game/card_search.html')


def card_query_view(request):
    """
    Handles user queries by providing card information.
    :param request:
    :return:
    """
    data = {}
    if request.GET:
        print('get request')
        query = request.GET.get('query', None)

        # Get cards by query
        monster_cards = MonsterCard.objects.filter(name__icontains=query)
        spell_cards = SpellCard.objects.filter(name__icontains=query)

        # Order by relevance

        # Prepare data
        data['monster_cards'] = {}
        data['spell_cards'] = {}
        for i, monster_card in enumerate(monster_cards):
            data['monster_cards'][i] = {
                'pk': monster_card.pk,
                'name': monster_card.name,
            }
        for i, spell_card in enumerate(spell_cards):
            data['spell_cards'][i] = {
                'pk': spell_card.pk,
                'name': spell_card.name,
            }


    # Send data as JSON
    return JsonResponse(data)

# Deck Views

class DeckCreateView(LoginRequiredMixin, CreateView):
    model = Deck
    form_class = DeckForm
    template_name = 'game/deck_create.html'
    success_url = '/game/deck_list.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return render(self.request, 'game/home.html')


@login_required
def deck_list_view(request):
    """
    Lists the User's Decks
    :param request:
    :return:
    """
    context = {
        'decks': Deck.objects.filter(user=request.user)
    }
    return render(request, 'game/deck_list.html', context)


@login_required
def deck_detail_view(request, pk):
    """
    Displays details of a User's Deck
    :param request:
    :return:
    """
    deck = Deck.objects.get(pk=pk)
    context = {
        'deck': deck.pk,
        'monster_cards': deck.monster_cards.all(),
        'spell_cards': deck.spell_cards.all(),
    }
    return render(request, 'game/deck_detail.html', context)


@login_required
def deck_add_monster_card_view(request):
    """
    Handles the adding of cards to a deck.
    Does not redirect.
    :param request:
    :param deck_pk:
    :return:
    """
    print('deck_add_monster_card_view')

    # Get POST information
    deck_pk = request.POST.get('deckPk', None)
    monster_card_pk = request.POST.get('cardPk', None)

    # Attempt to add card to deck
    deck = Deck.objects.get(pk=deck_pk)
    monster_card = MonsterCard.objects.get(pk=monster_card_pk)
    deck.add_card(monster_card)

    # Return the HTML resource we want to client to redirect to
    return JsonResponse({
        'success': True
    })


# GameState Views

@login_required
def host_view(request):
    """
    Creates GameState.
    Handles the creation of a room by a User who wants to create a game.
    :param request:
    :param room_name: uniquely identifies the room
    :return:
    """
    form = GameStateForm(request.POST or None)

    if request.POST:
        if form.is_valid():
            # If room already exists
            room_name = form.cleaned_data.get('room_name')
            if GameState.objects.filter(room_name=room_name).exists():
                messages.add_message(request, messages.ERROR, 'The room you are trying to host is occupied.')
                return redirect(reverse('game:home'))
            # Else room is available
            game_state = form.save()
            game_state.create_player_states()
            messages.add_message(request, messages.SUCCESS, 'Room created.')
            return redirect(reverse('game:home'))

        form = GameStateForm()

    context = {'form': form}
    return render(request, 'game/gamestate_create.html', context)


@login_required
def register_view(request):
    """
    Defines the parts of a GameState that need to be user-defined.
    Separate from host_view because definition of GameState depends on multiple users.
    Handles registration of a User into a room
    :param request:
    :param room_name:
    :return:
    """
    if request.POST:
        room_name = request.POST.get('room_name')

        # Attempt to register the user with game associated with room name
        game_state = GameState.objects.get(room_name=room_name)
        game_state.register(user=request.user)

    return redirect(reverse('game:room_list'))


@login_required
def room_list_view(request):
    """
    Lets User see a list of active rooms that he can join.
    :param request:
    :return:
    """
    games = GameState.objects.all()
    rooms = []

    for game in games:
        player_1 = game.player_1_state.user
        if player_1 is None:
            player_1_name = 'Free'
        else:
            player_1_name = player_1.username
        player_2 = game.player_2_state.user
        if player_2 is None:
            player_2_name = 'Free'
        else:
            player_2_name = player_2.username

        rooms.append(
            {
                'room_name': game.room_name,
                'player_1_name': player_1_name,
                'player_2_name': player_2_name,
            }
        )

    context = {
        'rooms': rooms
    }
    return render(request, 'game/room_list.html', context)


@login_required
def room_view(request, room_name):
    """
    Describe GameState to User.
    This view returns the interface that each User uses to play the game.
    A user accesses a game using room_name as key. This key will access a unique GameState model, which contains
    all information of the game.
    :param request:
    :param room_name: key to access a unique game
    :return:
    """
    game = GameState.objects.get(room_name=room_name)

    # Attempt to retrieve the game
    try:
        player_1_settings = UserSettings.objects.get(user=game.player_1_state.user)
        player_2_settings = UserSettings.objects.get(user=game.player_2_state.user)

        context = {
            'room_name': room_name,
            'is_started': game.is_started,
            'player_1_settings': player_1_settings,
            'player_2_settings': player_2_settings,
            'player_1_name': game.player_1_state.user.username,
            'player_2_name': game.player_2_state.user.username,
            'player_1_hp': game.player_1_state.hp,
            'player_2_hp': game.player_2_state.hp,
            'player_1_mana': game.player_1_state.mana,
            'player_2_mana': game.player_2_state.mana,
            'player_1_max_mana': game.player_1_state.max_mana,
            'player_2_max_mana': game.player_2_state.max_mana,
        }
    except Exception:
        messages.add_message(request, messages.ERROR, 'Unable to join room.')
        return render(request, 'game/home.html')

    return render(request, 'game/room.html', context)


@login_required
def user_settings_view(request):
    """
    Display and let Users update User-app specific settings.
    :param request:
    :return:
    """
    # Reference existing user settings. If DNE, create new settings.
    try:
        user_settings = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        user_settings = UserSettings.objects.create(user=request.user)

    # User POSTS user settings
    if request.POST:
        form = UserSettingsForm(request.POST, request.FILES)
        if form.is_valid():
            user_settings.preferred_deck = form.cleaned_data['preferred_deck']

            # Delete old picture
            user_settings.profile_picture.delete()

            # Update profile picture to new picture submitted via form
            user_settings.profile_picture = form.cleaned_data['profile_picture']

            user_settings.save()

            messages.add_message(request, messages.SUCCESS, 'User Settings Saved Successfully')
            return redirect(to=reverse('game:home'))
        else:
            print(form.errors)
    # User GETS user settings (or some other method other than POST)
    else:
        form = UserSettingsForm(instance=user_settings)

    context = {'form': form,
               'user_settings': user_settings}
    return render(request, 'game/user_settings.html', context)


# # TODO Implement Users uploading images and mp3.
# # TODO Can we combine this with user settings view?
# @login_required
# def upload_profile_picture_view(request):
#     """
#     Handles User uploading picture as form data
#     :param request:
#     :return:
#     """
#     if request.POST:
#         form = UploadImageForm(request.POST, request.FILES)
#         # if form.is_valid():
#     else:
#         form = UploadImageForm()
#
#     context = {'form': form}
#
#     return render(request, '')
