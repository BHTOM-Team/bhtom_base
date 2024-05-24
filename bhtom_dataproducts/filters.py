import django_filters
from django.conf import settings
from django.db.models import Q
from bhtom_base.bhtom_dataproducts.models import DataProduct

# Extracting choices from settings.DATA_PRODUCT_TYPES
DATA_PRODUCT_TYPE_CHOICES = [(v[1], v[1]) for k, v in settings.DATA_PRODUCT_TYPES.items()]

class DataProductFilter(django_filters.FilterSet):
    target_name = django_filters.CharFilter(label='Target Name', method='filter_target_name')
    observatory = django_filters.CharFilter(label='Observatory', method='filter_observatory_name')
    user = django_filters.CharFilter(label='Owner', method='filter_owner_name')
    status = django_filters.ChoiceFilter(label='Status', choices=DataProduct.STATUS)
    data_product_type = django_filters.ChoiceFilter(label='Type', choices=DATA_PRODUCT_TYPE_CHOICES, method='filter_data_product_type')
    created = django_filters.DateFromToRangeFilter(label='Upload date range')

    class Meta:
        model = DataProduct
        fields = [
            'target_name', 'observatory',
            'user', 'status',
            'data_product_type', 'created'
        ]

    def filter_target_name(self, queryset, name, value):
        return queryset.filter(Q(target__name__icontains=value))
    
    def filter_owner_name(self, queryset, name, value):
        return queryset.filter(Q(user__first_name__icontains=value))
    
    def filter_observatory_name(self, queryset, name, value):
        return queryset.filter(Q(observatory__camera__observatory__name__icontains=value))
    
    def filter_data_product_type(self, queryset, name, value):
        # Reverse mapping from display value to database value
        data_product_type_map = {v[1]: k for k, v in settings.DATA_PRODUCT_TYPES.items()}
        database_value = data_product_type_map.get(value)
        if database_value:
            return queryset.filter(Q(data_product_type__iexact=database_value))
        return queryset.none()
