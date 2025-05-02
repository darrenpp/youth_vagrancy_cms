from django.contrib import admin
from .models import (
    CensusRecord,
)


@admin.register(CensusRecord)
class CensusRecordAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'gender', 'electorate', 'date_recorded')
    search_fields = ('name', 'electorate')
    list_filter = ('gender', 'electorate')


