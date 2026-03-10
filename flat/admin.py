from django.contrib import admin
from .models import Transaction, Chore, RosterAssignment


admin.site.register(Chore)
admin.site.register(RosterAssignment)
admin.site.register(Transaction)
