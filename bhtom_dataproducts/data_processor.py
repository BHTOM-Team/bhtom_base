import mimetypes
from datetime import datetime
from typing import List, Tuple

from django.conf import settings
from importlib import import_module

from django.db import transaction

from bhtom_base.bhtom_dataproducts.models import ReducedDatum

from bhtom_base.bhtom_dataproducts.models import DatumValue, DataProduct

DEFAULT_DATA_PROCESSOR_CLASS = 'bhtom_base.bhtom_dataproducts.data_processor.DataProcessor'


def run_data_processor(dp):
    """
    Reads the `data_product_type` from the dp parameter and imports the corresponding `DataProcessor` specified in
    `settings.py`, then runs `process_data` and inserts the returned values into the database.

    :param dp: DataProduct which will be processed into a list
    :type dp: DataProduct

    :returns: QuerySet of `ReducedDatum` objects created by the `run_data_processor` call
    :rtype: `QuerySet` of `ReducedDatum`
    """

    try:
        processor_class = settings.DATA_PROCESSORS[dp.data_product_type]
    except Exception:
        processor_class = DEFAULT_DATA_PROCESSOR_CLASS

    try:
        mod_name, class_name = processor_class.rsplit('.', 1)
        mod = import_module(mod_name)
        clazz = getattr(mod, class_name)
    except (ImportError, AttributeError):
        raise ImportError('Could not import {}. Did you provide the correct path?'.format(processor_class))

    data_processor = clazz()
    data = list(set(data_processor.process_data(dp)))

    reduced_datums = [ReducedDatum(target=dp.target, data_product=dp, data_type=dp.data_product_type,
                                   timestamp=datum[0], mjd=datum[1].mjd, value=datum[1].value, error=datum[1].error,
                                   filter=datum[1].filter, observer=datum[1].observer,
                                   facility=datum[1].facility) for datum in data]
    with transaction.atomic():
        ReducedDatum.objects.bulk_create(reduced_datums)

    return ReducedDatum.objects.filter(data_product=dp)


class DataProcessor():

    FITS_MIMETYPES = ['image/fits', 'application/fits']
    PLAINTEXT_MIMETYPES = ['text/plain', 'text/csv']

    mimetypes.add_type('image/fits', '.fits')
    mimetypes.add_type('image/fits', '.fz')
    mimetypes.add_type('application/fits', '.fits')
    mimetypes.add_type('application/fits', '.fz')

    def process_data(self, data_product: DataProduct) -> List[Tuple[datetime, DatumValue]]:
        """
        Routes a photometry processing call to a method specific to a file-format. This method is expected to be
        implemented by any subclasses.

        :param data_product: DataProduct which will be processed into a list
        :type data_product: DataProduct

        :returns: python list of 2-tuples, each with a timestamp and corresponding data
        :rtype: list of 2-tuples
        """
        return []
