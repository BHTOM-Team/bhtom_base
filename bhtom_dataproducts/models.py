import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from PIL import Image
from astropy.io import fits
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _
from fits2image.conversions import fits_to_jpg

from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix
from bhtom_base.bhtom_observations.models import ObservationRecord
from bhtom_base.bhtom_targets.models import Target

logger = logging.getLogger(__name__)

try:
    THUMBNAIL_DEFAULT_SIZE = settings.THUMBNAIL_DEFAULT_SIZE
except AttributeError:
    THUMBNAIL_DEFAULT_SIZE = (200, 200)


class ReducedDatumUnit(models.TextChoices):
    MAGNITUDE = 'MAG', _('mag')
    MILLIJANSKY = 'MILLIJANSKY', _('mJy')
    ERG_S_CM2_ANGSTROM = 'ERG_S_CM2_ANGSTROM', _('erg/s/cm^2/Angstrom')


def find_fits_img_size(filename):
    """
    Returns the size of a FITS image, given a valid FITS image file

    :param filename: The fully-qualified path of the FITS image file
    :type filename: str

    :returns: Tuple of horizontal/vertical dimensions
    :rtype: tuple
    """

    try:
        return settings.THUMBNAIL_MAX_SIZE
    except AttributeError:
        hdul = fits.open(filename)
        xsize = 0
        ysize = 0
        for hdu in hdul:
            try:
                xsize = max(xsize, hdu.header['NAXIS1'])
                ysize = max(ysize, hdu.header['NAXIS2'])
            except KeyError:
                pass
        return (xsize, ysize)


def is_fits_image_file(file):
    """
    Checks if a file is a valid FITS image by checking if any header contains 'SCI' in the 'EXTNAME'.

    :param file: The file to be checked.
    :type file:

    :returns: True if the file is a FITS image, False otherwise
    :rtype: boolean
    """

    with file.open() as f:
        try:
            hdul = fits.open(f)
        except OSError:  # OSError is raised if file is not FITS format
            return False
        for hdu in hdul:
            if hdu.header.get('EXTNAME') == 'SCI':
                return True
    return False


def data_product_path(instance, filename):
    """
    Returns the TOM-style path for a ``DataProduct`` file. Structure is <target identifier>/<facility>/<filename>.
    ``DataProduct`` objects not associated with a facility will save with 'None' as the facility.

    :param instance: The specific instance of the ``DataProduct`` class.
    :type instance: DataProduct

    :param filename: The filename to add to the path.
    :type filename: str

    :returns: The TOM-style path of the file
    :rtype: str
    """
    # Uploads go to MEDIA_ROOT
    data = 'data'

    if instance.data_product_type == settings.DATA_PRODUCT_TYPES['photometry'][0] or \
            instance.data_product_type == settings.DATA_PRODUCT_TYPES['photometry_nondetection'][0]:
        data = 'photometry'
    elif instance.data_product_type == settings.DATA_PRODUCT_TYPES['fits_file'][0]:
        return 'fits/{0}/{1}'.format(instance.target.name, filename)

    if instance.observation_record is not None:
        return 'targets/{0}/{1}/{2}/{3}'.format(instance.target.name, instance.observation_record.facility, data, filename)
    else:
        return 'targets/{0}/user/{1}/{2}'.format(instance.target.name, data, filename)


class DataProductGroup(models.Model):
    """
    Class representing a group of ``DataProduct`` objects in a TOM.

    :param name: The name of the group of ``DataProduct`` objects
    :type name: str

    :param created: The time at which this object was created.
    :type created: datetime

    :param modified: The time at which this object was last changed.
    :type modified: datetime
    """
    name = models.CharField(max_length=200, unique=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)
    private = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.name


class DataProductGroup_user(models.Model):
    """
    Class representing a group of user in dataproduct group.
    """

    group = models.ForeignKey(DataProductGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    owner = models.BooleanField(default=False, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    active_flg = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.user.username


class DataProduct(models.Model):
    """
    Class representing a data product object in a TOM.

    A DataProduct corresponds to any file containing data, from a FITS, to a PNG, to a CSV. It can optionally be
    associated with a specific observation, and is required to be associated with a target.

    :param product_id: The identifier of the data product used by its original source.
    :type product_id: str

    :param target: The ``Target`` with which this object is associated.
    :type target: Target

    :param observation_record: The ``ObservationRecord`` with which this object is optionally associated.
    :type observation_record: ObservationRecord

    :param data: The file this object refers to.
    :type data: django.core.files.File

    :param extra_data: Arbitrary text field for storing additional information about this object.
    :type extra_data: str

    :param group: Set of ``DataProductGroup`` objects this object is associated with.
    :type DataProductGroup:

    :param created: The time at which this object was created.
    :type created: datetime

    :param modified: The time at which this object was last modified.
    :type modified: datetime

    :param data_product_type: The type of data referred to by this object. Default options are photometry, fits_file,
        spectroscopy, or image_file. Can be configured in settings.py.
    :type data_product_type: str

    :param featured: Whether or not the data product is intended to be featured, used by default on the target detail
        page as a "display" option. Only one ``DataProduct`` can be featured per ``Target``.
    :type featured: boolean

    :param thumbnail: The thumbnail file associated with this object. Only generated for FITS image files.
    :type thumbnail: FileField
    """
    STATUS = [
        ('C', 'TO DO'),
        ('P', 'IN PROGRESS'),
        ('S', 'SUCCESS'),
        ('E', 'ERROR')
    ]

    FITS_EXTENSIONS = {
        '.fits': 'PRIMARY',
        '.fz': 'SCI'
    }

    product_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        help_text='Data product identifier used by the source of the data product.'
    )
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    observation_record = models.ForeignKey(ObservationRecord, null=True, default=None, on_delete=models.CASCADE)
    observatory = models.ForeignKey(ObservatoryMatrix, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, default=None, on_delete=models.SET_NULL)
    data = models.FileField(upload_to=data_product_path, null=True, default='')
    status = models.CharField(max_length=1, choices=STATUS, default='C')
    photometry_data = models.URLField(null=True, default=None)
    fits_data = models.URLField(null=True, default=None)
    extra_data = models.TextField(blank=True, default='')
    group = models.ManyToManyField(DataProductGroup)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)
    data_product_type = models.CharField(max_length=50, blank=True, default='', db_index=True)
    featured = models.BooleanField(default=False)
    thumbnail = models.FileField(upload_to=data_product_path, null=True, default=None)
    dryRun = models.BooleanField(default=False, verbose_name='Dry Run (no data will be stored in the database)')
    comment = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('-created',)
        get_latest_by = ('modified',)

    def __str__(self):
        return self.data.name

    def save(self, *args, **kwargs):
        """
        Saves the current `DataProduct` instance. Before saving, validates the `data_product_type` against those
        specified in `settings.py`.
        """
        for _, dp_values in settings.DATA_PRODUCT_TYPES.items():
            if not self.data_product_type or self.data_product_type == dp_values[0]:
                break
        else:
            raise ValidationError('Not a valid DataProduct type.')
        return super().save()

    def get_type_display(self):
        """
        Gets the corresponding display value for a data_product_type.

        :returns: Display value for a given data_product_type.
        :rtype: str
        """
        return settings.DATA_PRODUCT_TYPES[self.data_product_type][1]

    def get_file_name(self):
        return os.path.basename(self.data.name)

    def get_file_extension(self):
        """
        Returns the extension of the file associated with this data product

        :returns: File extension
        :rtype: str
        """
        return os.path.splitext(self.data.name)[1]

    def get_preview(self, size=THUMBNAIL_DEFAULT_SIZE, redraw=False):
        """
        Returns path to the thumbnail of this data product, and creates a thumbnail if none exists

       :Keyword Arguments:
            * size (`tuple`): Desired size of the thumbnail, as a 2-tuple of ints for width/height
            * redraw (`boolean`): True if the thumbnail will be recreated despite existing, False otherwise

        :returns: Path to the thumbnail image
        :rtype: str
        """
        if self.thumbnail:
            im = Image.open(self.thumbnail)
            if im.size != THUMBNAIL_DEFAULT_SIZE:
                redraw = True

        if not self.thumbnail or redraw:
            width, height = THUMBNAIL_DEFAULT_SIZE
            tmpfile = self.create_thumbnail(width=width, height=height)
            if tmpfile:
                outfile_name = os.path.basename(self.data.file.name)
                filename = outfile_name.split(".")[0] + "_tb.jpg"
                with open(tmpfile.name, 'rb') as f:
                    self.thumbnail.save(filename, File(f), save=True)
                    self.save()
        if not self.thumbnail:
            return None
        return self.thumbnail.url

    def create_thumbnail(self, width=None, height=None):
        """
        Creates a thumbnail image of this data product (if it is a valid FITS image file) with specified width and
        height, or the original width and height if none is specified.

        :Keyword Arguments:
            * width (`int`): Desired width of the thumbnail
            * height (`int`): Desired height of the thumbnail

        :returns: Thumbnail file if created, None otherwise
        :rtype: file
        """
        if is_fits_image_file(self.data.file):
            tmpfile = tempfile.NamedTemporaryFile(suffix='.jpg')
            try:
                if not width or not height:
                    width, height = find_fits_img_size(self.data.file)
                resp = fits_to_jpg(self.data.file, tmpfile.name, width=width, height=height)
                if resp:
                    return tmpfile
            except Exception as e:
                logger.warn(f'Unable to create thumbnail for {self}: {e}')
        return


class ReducedDatum(models.Model):
    """
    Class representing a datum in a TOM.

    A ``ReducedDatum`` generally refers to a single piece of data--e.g., a spectrum, or a photometry point. It is
    associated with a target, and optionally with the data product it came from. An example of a ``ReducedDatum``
    without an associated data product would be photometry ingested from a broker.

    :param target: The ``Target`` with which this object is associated.

    :param user: The ``User`` who added this reduced datum.

    :param data_product: The ``DataProduct`` with which this object is optionally associated.

    :param data_type: The type of data this datum represents. Default choices are the default values found in
        DATA_PRODUCT_TYPES in settings.py.
    :type data_type: str

    :param source_name: The original source of this datum. The current major use of this field is to track the broker a
                        datum came from, but can be used for other sources.
    :type source_name: str

    :param source_location: A reference to the location that this datum was originally sourced from. The current major
                            use of this field is the URL path to the alert that this datum came from.
    :type source_name: str

    :param mjd: the MJD timestamp of this datum.
    :type mjd: float

    :param timestamp: The timestamp of this datum.
    :type timestamp: datetime

    :param observer: The name of the observer or survey who took this datum.
    :type observer: str

    :param facility: The name of the facility this dataproduct was observed with.
    :type facility: str

    :param value: The value of the datum (e.g. magnitude, mag limit, flux, etc.)
    :type value: float

    :param value_list: The array of values, e.g. fluxes for spectra
    :type value_list: array

    :param value_unit: The unit of value (e.g. magnitude, mJy, etc.)
    :type value: str

    :param error: The value error of the datum (e.g. magnitude, flux, etc.)
    :type error: float

    :param error_list: The array of error values, e.g. flux errors for spectra
    :type error_list: array

    :param filter: Filterband, but also wavelength for spectra etc.
    :type filter: str

    :param wavelengths: The array of wavelengths for spectra
    :type wavelengths: array

    :param extra_data: Additional value of the datum. This is a dict, intended to store data with a variety of scopes.
                       For example, that could be HJD or a comment.
    :type extra_data: dict

    """

    target = models.ForeignKey(Target, null=False, on_delete=models.CASCADE)
    data_product = models.ForeignKey(DataProduct, null=True, blank=True, on_delete=models.CASCADE)
    data_type = models.CharField(
        max_length=100,
        default=''
    )
    source_name = models.CharField(max_length=100, default='', db_index=True)
    source_location = models.CharField(max_length=200,blank=True, default='')
    mjd = models.FloatField(null=False, default=0)
    timestamp = models.DateTimeField(null=False, blank=False, default=datetime.now, db_index=True)
    observer = models.CharField(null=False, max_length=100, default='')
    facility = models.CharField(null=False, max_length=100, default='')
    value = models.FloatField(null=False, default=100)
    value_list = ArrayField(models.FloatField(), null=True, blank=True, default=list)
    value_unit = models.CharField(
        max_length=100,
        choices=ReducedDatumUnit.choices,
        default=ReducedDatumUnit.MAGNITUDE
    )
    error = models.FloatField(null=False, default=1)
    error_list = ArrayField(models.FloatField(), null=True,blank=True, default=list)
    filter = models.CharField(max_length=100, null=False, default='')
    wavelengths = ArrayField(models.FloatField(), null=True,blank=True, default=list)
    extra_data = models.JSONField(null=True, blank=True)
    active_flg = models.BooleanField(default=True)

    class Meta:
        unique_together = (('target', 'mjd', 'value', 'error', 'filter', 'facility', 'observer'),)
        get_latest_by = ('mjd',)

    def save(self, *args, **kwargs):
        for _, dp_values in settings.DATA_PRODUCT_TYPES.items():
            if self.data_type and self.data_type == dp_values[0]:
                break
        else:
            raise ValidationError('Not a valid DataProduct type.')

        return super().save()


@dataclass(frozen=True)
class DatumValue:
    """
    A helper class for data processor results
    """
    mjd: float
    value: float
    observer: Optional[str] = None
    facility: Optional[str] = None
    error: Optional[float] = None
    filter: Optional[str] = None
    data_type: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class BrokerCadence(models.Model):
    target = models.ForeignKey(Target, null=False, on_delete=models.CASCADE)
    broker_name = models.CharField(null=False, max_length=50)
    last_update = models.DateTimeField(null=True, blank=True)
    insert_row = models.IntegerField(null=True, default=0)

    class Meta:
        unique_together = (('target', 'broker_name'),)


class CCDPhotJob(models.Model):
    JOB_STATUS_CHOICES = [
        ('P', 'Preparation'),
        ('R', 'Running'),
        ('F', 'Finished'),  # ccdphot finished, result not extracted
        ('D', 'Done'),  # results sed back
        ('E', 'Error'),  # ccdphot finished with error
    ]
    dataProduct = models.ForeignKey(DataProduct, null=False, on_delete=models.CASCADE)
    job_id = models.CharField(db_index=True, max_length=50)
    instrument = models.CharField(max_length=100, blank=True,
                                  help_text='instrument identification (not used by ccdphot)')
    instrument_prefix = models.CharField(max_length=50, blank=True,
                                         help_text='instrument prefix used to chose proper obsinfo')
    webhook_id = models.CharField(max_length=20, blank=True,
                                  help_text='id of webhook to be fired after ccdphot processing (not implemented yet)')
    target_name = models.CharField(max_length=100, blank=True, help_text='name of the target from BHTOM')
    target_ra = models.FloatField(default=0.0, null=True, help_text='ra in decimal format')
    target_dec = models.FloatField(default=0.0, null=True, help_text='dec in decimal format')
    username = models.CharField(max_length=150, blank=True, help_text='BHTOM username')
    hashtag = models.CharField(max_length=255, blank=True, help_text='CPCS hashtag')
    dry_run = models.CharField(max_length=5, blank=True, default="False",
                               help_text='in format of "True" or "False" string')
    fits_id = models.IntegerField(default=-1, null=True, help_text='ID of the BHTOM fits file')
    priority = models.IntegerField(default=0, help_text='default = 0, lower number - higher priority')
    start_time = models.DateTimeField(auto_now_add=True, db_index=True)
    status_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, editable=False, choices=JOB_STATUS_CHOICES, default='P')
    status_message = models.TextField(default='job created', blank=True, editable=False)
    progress = models.FloatField(default=0.0, editable=False)
    fits_file = models.FileField(upload_to='fits')
    ccdphot_result = models.TextField(null=True, blank=True, editable=False)
    ccdphot_result_file = models.TextField(null=True, blank=True, editable=False)
    ccdphot_stdout_file = models.TextField(null=True, blank=True, editable=False)

    fits_object = models.CharField(max_length=70, null=True)
    fits_ra = models.FloatField(default=0.0, null=True)
    fits_dec = models.FloatField(default=0.0, null=True)
    fits_mjd = models.FloatField(default=0.0, null=True)
    fits_hjd = models.FloatField(default=0.0, null=True)
    fits_exp = models.FloatField(default=0.0, null=True)
    fits_filter = models.CharField(max_length=70, null=True)
    fits_origin = models.CharField(max_length=70, null=True)
    fits_observat = models.CharField(max_length=70, null=True)
    fits_telescop = models.CharField(max_length=70, null=True)
    fits_instrume = models.CharField(max_length=70, null=True)
    fits_observer = models.CharField(max_length=70, null=True)
