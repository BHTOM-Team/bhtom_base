
import csv

from bhtom2.utils.bhtom_logger import BHTOMLogger
from .models import Target, TargetExtra, TargetName
from io import StringIO
from django.db.models import ExpressionWrapper, FloatField
from django.db.models.functions.math import ACos, Cos, Radians, Pi, Sin
from django.conf import settings
from math import radians
from bhtom_base.bhtom_common.hooks import run_hook
from django.forms.models import model_to_dict

logger: BHTOMLogger = BHTOMLogger(__name__, 'bhtom: utils')


# NOTE: This saves locally. To avoid this, create file buffer.
# referenced https://www.codingforentrepreneurs.com/blog/django-queryset-to-csv-files-datasets/
def export_targets(qs):
    """
    Exports all the specified targets into a csv file in folder csvTargetFiles
    NOTE: This saves locally. To avoid this, create file buffer.

    :param qs: List of targets to export
    :type qs: QuerySet

    :returns: String buffer of exported targets
    :rtype: StringIO
    """
    qs_pk = [data.id for data in qs]
    data_list = list(qs)
    target_fields = [field.name for field in Target._meta.get_fields()]
    target_extra_fields = list({field.key for field in TargetExtra.objects.filter(target__in=qs_pk)})
    
    all_fields = target_fields + target_extra_fields + [f'{sn.upper()}_name' for sn in
                                                     set(TargetName.objects.filter(target__in=qs_pk).values_list('source_name', flat=True))]
    for key in ['id','brokercadence', 'dr3', 'dr2', 'targetlist', 'dataproduct', 'observationrecord', 'reduceddatum',
                'aliases', 'targetextra', 'photometry_plot', 'photometry_plot_obs', 'photometry_icon_plot',
                'spectroscopy_plot', 'data_plot', 'modified', 'created', 'spectroscopydatum', 'atlasqueue']:
        try:
            all_fields.remove(key)
        except Exception as e:
            logger.warning(f'Could not remove {key}: {e}')

    file_buffer = StringIO()
    writer = csv.DictWriter(file_buffer, fieldnames=all_fields)
    writer.writeheader()
    
    for target_data in data_list:
        # Convert the Target object to a dictionary
        target_dict = model_to_dict(target_data, fields=target_fields)

        # Add extra fields from TargetExtra
        for e in TargetExtra.objects.filter(target_id=target_data.id):
            target_dict[e.key] = e.value
        
        # Add name fields from TargetName
        for name in TargetName.objects.filter(target_id=target_data.id):
            target_dict[f'{name.source_name.upper()}_name'] = name.name

        # Remove unnecessary fields
        for key in ['id','brokercadence','dr3','dr2', 'targetlist', 'dataproduct', 'observationrecord', 'reduceddatum', 'aliases', 'targetextra', 'photometry_plot', 'photometry_plot_obs', 'photometry_icon_plot', 'spectroscopy_plot', 'data_plot', 'modified','created']:
            if key in target_dict:
                del target_dict[key]
        writer.writerow(target_dict)

    return file_buffer

def import_targets(targets):
    """
    Imports a set of targets into the TOM and saves them to the database.

    Additionally, performs post hook for each target (names, creation date)

    :param targets: String buffer of targets
    :type targets: StringIO

    :returns: dictionary of successfully imported targets, as well errors
    :rtype: dict
    """
    # TODO: Replace this with an in memory iterator
    targetreader = csv.DictReader(targets, dialect=csv.excel)
    targets = []
    errors = []
    base_target_fields = [field.name for field in Target._meta.get_fields()]
    for index, row in enumerate(targetreader):
        # filter out empty values in base fields, otherwise converting empty string to float will throw error
        row = {k.strip(): v.strip() for (k, v) in row.items() if not (k.strip() in base_target_fields and not v.strip())}
        target_extra_fields = []
        target_names = {}
        target_fields = {}

        #gets all possible source names, written in upper case
        uppercase_source_names = [sc[0].upper() for sc in settings.SOURCE_CHOICES]

        for k in row:
            # Fields with <source_name>_name (e.g. Gaia_name, ZTF_name, where <source_name> is a valid
            # catalog) will be added as a name corresponding to this catalog
            k_source_name = k.upper().replace('_NAME', '')
            if k != 'name' and k.endswith('name') and k_source_name in uppercase_source_names:
                target_names[k_source_name] = row[k]
            elif k not in base_target_fields:
                target_extra_fields.append((k, row[k]))
            else:
                target_fields[k] = row[k]
        for extra in target_extra_fields:
            row.pop(extra[0])
        try:
            target = Target.objects.create(**target_fields)
            for extra in target_extra_fields:
                TargetExtra.objects.create(target=target, key=extra[0], value=extra[1])
            for name in target_names.items():
                if name:
                    source_name = name[0].upper().replace('_NAME', '')
                    TargetName.objects.create(target=target, source_name=source_name, name=name[1])

            run_hook('target_post_save', target=target, created=True)

            targets.append(target)
        except Exception as e:
            error = 'Error on line {0}: {1}'.format(index + 2, str(e))
            errors.append(error)

    return {'targets': targets, 'errors': errors}


from astropy.coordinates import SkyCoord
from astropy import units as u

def cone_search_filter(queryset, ra, dec, radius):
    """
    Executes cone search by annotating each target with separation distance from the specified RA/Dec.
    Uses astropy for accurate spherical calculations.

    :param queryset: Queryset of Target objects
    :type queryset: Target

    :param ra: Right ascension of center of cone in degrees.
    :type ra: float

    :param dec: Declination of center of cone in degrees.
    :type dec: float

    :param radius: Radius of cone search in degrees.
    :type radius: float
    """
    # Convert input coordinates to SkyCoord object
    center_coord = SkyCoord(ra=ra * u.degree, dec=dec * u.degree, frame='icrs')

    # Filter initial square box to reduce dataset size
    double_radius = radius * 2
    queryset = queryset.filter(
        ra__gte=ra - double_radius, ra__lte=ra + double_radius,
        dec__gte=dec - double_radius, dec__lte=dec + double_radius
    )
    matching_ids = []
    for target in queryset:
        target_coord = SkyCoord(ra=target.ra * u.degree, dec=target.dec * u.degree, frame='icrs')
        separation = center_coord.separation(target_coord)
        if separation.degree <= radius:
            matching_ids.append(target.id)
    return queryset.filter(id__in=matching_ids)



