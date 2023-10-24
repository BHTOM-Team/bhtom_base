import django_filters
from django.db.models import Q

from bhtom_base.bhtom_dataproducts.models import DataProduct


class DataProductFilter(django_filters.FilterSet):
    target_name = django_filters.CharFilter(label='Target Name', method='filter_name')

    class Meta:
        model = DataProduct
        fields = ['target_name']

    def filter_name(self, queryset, name, value):
        return queryset.filter(Q(target__name__icontains=value))
