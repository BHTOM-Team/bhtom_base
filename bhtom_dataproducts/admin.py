import os

import requests
from django.contrib import admin
from django_guid import get_guid
from dotenv import dotenv_values

from bhtom2.settings import BASE_DIR
from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_dataproducts.models import DataProduct, DataProductGroup, ReducedDatum

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_dataprocucts.admin')


class ReducedDatumAdmin(admin.ModelAdmin):
    model = ReducedDatum
    list_display = ['target', 'data_product', 'data_type', 'source_name', 'observer', 'facility', 'value', 'value_unit',
                    'active_flg', 'timestamp']
    list_filter = ['facility', 'data_type', 'source_name', 'target__name', 'timestamp']
    search_fields = ['mjd', 'observer', 'facility', 'value']

    def disable_reducedDatum(self, request, queryset):
        queryset.update(active_flg=False)
        for row in queryset:
            target = row.target.name
            updatePlot(target)

    actions = [disable_reducedDatum]


def updatePlot(targetName):
    secret = dotenv_values(os.path.join(BASE_DIR, 'bhtom2/.bhtom.env'))

    try:
        guid = get_guid()
        requests.post(secret.get('CPCS_URL') + '/updatePlot/', json={'name': targetName},
                      headers={"Correlation-ID": guid})
        logger.debug("Update Plot for: %s successfully" % str(targetName))

    except Exception as e:
        logger.error("Update plot error: %s" % str(e))


admin.site.register(DataProduct)
admin.site.register(DataProductGroup)
admin.site.register(ReducedDatum, ReducedDatumAdmin)
