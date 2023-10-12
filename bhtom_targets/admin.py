from django.contrib import admin

from bhtom_base.bhtom_targets.forms import TargetNamesFormset
from .models import Target, TargetList, TargetExtra, TargetName
from bhtom2.bhtom_targets.utils import get_nonempty_names_from_queryset
from ..bhtom_common.hooks import run_hook


class TargetExtraInline(admin.TabularInline):
    model = TargetExtra
    exclude = ('float_value', 'bool_value', 'time_value')
    extra = 0


class TargetNameInline(admin.TabularInline):
    model = TargetName
    list_display = ['source_name', 'name']


class TargetAdmin(admin.ModelAdmin):
    model = Target
    inlines = [TargetNameInline]
    list_display = ['name', 'type', 'created', 'modified']
    list_filter = ['type']
    search_fields = ['name']

    def save_model(self, request, obj, form, change):

        names = TargetNamesFormset(form.data)
        target_names = get_nonempty_names_from_queryset(names.data)

        for broker, name in target_names:
            run_hook('update_alias', target=obj, broker=broker)

        super().save_model(request, obj, form, change)


class TargetListAdmin(admin.ModelAdmin):
    model = TargetList


admin.site.register(Target, TargetAdmin)

admin.site.register(TargetList, TargetListAdmin)
