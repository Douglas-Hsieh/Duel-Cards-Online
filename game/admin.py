from django.contrib import admin

from .models import Card, MonsterCard, SpellCard
# Register your models here.

admin.site.register(MonsterCard)
admin.site.register(SpellCard)
