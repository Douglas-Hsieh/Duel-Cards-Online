# Django Form classes

# ModelForm generalizes form handing
# Instead of creating a form, collecting data, associating that data to fields in a database:
# Our models induce what we have in our forms.
# Thus ModelForms contain a subset of a model's fields information

from django import forms
from .models import Card, MonsterCard, SpellCard, Deck, GameState, UserSettings


class CardForm(forms.ModelForm):
    """
    Form for users to create cards
    """
    class Meta:
        model = Card
        fields = [
            'name',
            'description',
            'cost',
            'picture',
        ]


class MonsterCardForm(CardForm):
    class Meta(CardForm.Meta):
        model = MonsterCard  # We specify model so that we know what fields to expect in the form
        fields = CardForm.Meta.fields + [
            'attack',
            'hp',
        ]
        # exclude = ['type',]


class SpellCardForm(CardForm):
    class Meta(CardForm.Meta):
        model = SpellCard
        fields = CardForm.Meta.fields + [
            'effect',
        ]


class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = [
            'name',
        ]


class GameStateForm(forms.ModelForm):
    class Meta:
        model = GameState
        fields = [
            'room_name',
        ]


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            'preferred_deck', 'profile_picture',
        ]



