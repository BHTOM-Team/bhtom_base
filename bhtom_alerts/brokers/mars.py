from datetime import datetime
from typing import Tuple, List

import requests
from django.db import transaction
from requests.exceptions import HTTPError
from urllib.parse import urlencode
from dateutil.parser import parse
from django import forms
from crispy_forms.layout import Layout, Div, Fieldset, HTML
from astropy.time import Time, TimezoneInfo

from bhtom2.utils.bhtom_logger import BHTOMLogger
from bhtom_base.bhtom_alerts.alerts import GenericAlert, GenericBroker, GenericQueryForm
from bhtom_base.bhtom_targets.models import Target
from bhtom_base.bhtom_dataproducts.models import ReducedDatum, DatumValue

MARS_URL = 'https://mars.lco.global'
filters = {1: 'g', 2: 'r', 3: 'i'}


logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom:MARS Lightcurve Update')


class MARSQueryForm(GenericQueryForm):
    objectId = forms.CharField(required=False, label='ZTF Object ID')
    time__gt = forms.CharField(
        required=False,
        label='Time Lower',
        widget=forms.TextInput(attrs={'type': 'date'})
    )
    time__lt = forms.CharField(
        required=False,
        label='Time Upper',
        widget=forms.TextInput(attrs={'type': 'date'})
    )
    time__since = forms.IntegerField(
        required=False,
        label='Time Since',
        help_text='Alerts younger than this number of seconds'
    )
    jd__gt = forms.FloatField(required=False, label='JD Lower')
    jd__lt = forms.FloatField(required=False, label='JD Upper')
    filter = forms.CharField(required=False)
    cone = forms.CharField(
        required=False,
        label='Cone Search',
        help_text='RA,Dec,radius in degrees'
    )
    objectcone = forms.CharField(
        required=False,
        label='Object Cone Search',
        help_text='Object name,radius in degrees'
    )
    objectidps = forms.CharField(
        required=False,
        label='Nearby Objects',
        help_text='Id from PS1 catalog'
    )
    ra__gt = forms.FloatField(required=False, label='RA Lower')
    ra__lt = forms.FloatField(required=False, label='RA Upper')
    dec__gt = forms.FloatField(required=False, label='Dec Lower')
    dec__lt = forms.FloatField(required=False, label='Dec Upper')
    l__gt = forms.FloatField(required=False, label='l Lower')
    l__lt = forms.FloatField(required=False, label='l Upper')
    b__gt = forms.FloatField(required=False, label='b Lower')
    b__lt = forms.FloatField(required=False, label='b Upper')
    magpsf__gte = forms.FloatField(required=False, label='Magpsf Lower')
    magpsf__lte = forms.FloatField(required=False, label='Magpsf Upper')
    sigmapsf__lte = forms.FloatField(required=False, label='Sigmapsf Upper')
    magap__gte = forms.FloatField(required=False, label='Magap Lower')
    magap__lte = forms.FloatField(required=False, label='Magap Upper')
    distnr__gte = forms.FloatField(required=False, label='Distnr Lower')
    distnr__lte = forms.FloatField(required=False, label='Distnr Upper')
    deltamaglatest__gte = forms.FloatField(
        required=False,
        label='Delta Mag Lower'
    )
    deltamaglatest__lte = forms.FloatField(
        required=False,
        label='Delta Mag Upper'
    )
    deltamagref__gte = forms.FloatField(
        required=False,
        label='Delta Mag Ref Lower'
    )
    deltamagref__lte = forms.FloatField(
        required=False,
        label='Delta Mag Ref Upper'
    )
    rb__gte = forms.FloatField(required=False, label='Real/Bogus Lower')
    drb__gte = forms.FloatField(required=False, label='Deep-Learning Real/Bogus Lower')
    classtar__gte = forms.FloatField(required=False, label='Classtar Lower')
    classtar__lte = forms.FloatField(required=False, label='Classtar Upper')
    fwhm__lte = forms.FloatField(required=False, label='FWHM Upper')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            HTML('''
                <p>
                Please see <a href="https://mars.lco.global/help">MARS help</a>
                for a detailed description of available filters.
                </p>
            '''),
            self.common_layout,
            'objectId',
            Fieldset(
                'Time based filters',
                'time__since',
                Div(
                    Div(
                        'time__gt',
                        'jd__gt',
                        css_class='col',
                    ),
                    Div(
                        'time__lt',
                        'jd__lt',
                        css_class='col',
                    ),
                    css_class="form-row",
                )
            ),
            Fieldset(
                'Location based filters',
                'cone',
                'objectcone',
                'objectidps',
                Div(
                    Div(
                        'ra__gt',
                        'dec__gt',
                        'l__gt',
                        'b__gt',
                        css_class='col',
                    ),
                    Div(
                        'ra__lt',
                        'dec__lt',
                        'l__lt',
                        'b__lt',
                        css_class='col',
                    ),
                    css_class="form-row",
                )
            ),
            Fieldset(
                'Other Filters',
                Div(
                    Div(
                        'magpsf__gte',
                        'magap__gte',
                        'distnr__gte',
                        'deltamaglatest__gte',
                        'deltamagref__gte',
                        'classtar__gte',
                        css_class='col'
                    ),
                    Div(
                        'magpsf__lte',
                        'magap__lte',
                        'distnr__lte',
                        'deltamaglatest__lte',
                        'deltamagref__lte',
                        'classtar__lte',
                        css_class='col'
                    ),
                    css_class='form-row',
                )
            ),
            'filter',
            'sigmapsf__lte',
            'rb__gte',
            'drb__gte',
            'fwhm__lte'
        )


class MARSBroker(GenericBroker):
    """
    The ``MARSBroker`` is the interface to the MARS alert broker. For information regarding MARS and its available
    filters for querying, please see https://mars.lco.global/help/.
    """

    name = 'MARS'
    form = MARSQueryForm

    def _clean_parameters(self, parameters):
        return {k: v for k, v in parameters.items() if v and k != 'page'}

    def _request_alerts(self, parameters):
        if not parameters.get('page'):
            parameters['page'] = 1
        args = urlencode(self._clean_parameters(parameters))
        url = '{0}/?page={1}&format=json&{2}'.format(
            MARS_URL,
            parameters['page'],
            args
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_alerts(self, parameters):
        response = self._request_alerts(parameters)
        alerts = response['results']
        if response['has_next'] and parameters['page'] < 10:
            parameters['page'] += 1
            alerts += self.fetch_alerts(parameters)
        return iter(alerts)

    def fetch_alert(self, id):
        url = f'{MARS_URL}/{id}/?format=json'
        response = requests.get(url)
        response.raise_for_status()
        parsed = response.json()
        return parsed

    def process_reduced_data(self, target, alert=None):
        if not alert:
            try:
                target_datum = ReducedDatum.objects.filter(
                    target=target,
                    data_type='photometry',
                    source_name=self.name).first()
                if not target_datum:
                    return
                alert = self.fetch_alert(target_datum.source_location)
            except HTTPError:
                raise Exception('Unable to retrieve alert information from broker')
        if not alert.get('prv_candidate'):
            alert = self.fetch_alert(alert['lco_id'])

        candidates = [{'candidate': alert.get('candidate')}] + alert.get('prv_candidate')

        data: List[Tuple[datetime, DatumValue]] = []

        for candidate in candidates:
            if all([key in candidate['candidate'] for key in ['jd', 'magpsf', 'fid', 'sigmapsf']]):
                nondetection = False
            elif all(key in candidate['candidate'] for key in ['jd', 'diffmaglim', 'fid']):
                nondetection = True
            else:
                continue
            jd = Time(candidate['candidate']['jd'], format='jd', scale='utc')

            error = None

            if nondetection:
                value = candidate['candidate']['diffmaglim']
                data_type = 'photometry_nondetection'
            else:
                value = candidate['candidate']['magpsf']
                error = candidate['candidate']['sigmapsf']
                data_type = 'photometry'

            data.append((jd.to_datetime(timezone=TimezoneInfo()),
                         DatumValue(mjd=jd.mjd,
                                    value=value,
                                    error=error,
                                    data_type=data_type,
                                    filter=filters[candidate['candidate']['fid']])))

        data = list(set(data))
        reduced_data = [ReducedDatum(target=target,
                                     data_type=datum[1].data_type,
                                     timestamp=datum[0],
                                     mjd=datum[1].mjd,
                                     value=datum[1].value,
                                     source_name=self.name,
                                     source_location=alert['lco_id'],
                                     error=datum[1].error,
                                     filter=datum[1].filter,
                                     observer='ZTF',
                                     facility='ZTF') for datum in data]
        with transaction.atomic():
            ReducedDatum.objects.bulk_create(reduced_data, ignore_conflicts=True)

    def to_target(self, alert):
        alert_copy = alert.copy()
        target = Target.objects.create(
            name=alert_copy['objectId'],
            type='SIDEREAL',
            ra=alert_copy['candidate'].pop('ra'),
            dec=alert_copy['candidate'].pop('dec'),
            galactic_lng=alert_copy['candidate'].pop('l'),
            galactic_lat=alert_copy['candidate'].pop('b'),
        )
        return target

    def to_generic_alert(self, alert):
        timestamp = parse(alert['candidate']['wall_time'])
        url = '{0}/{1}/'.format(MARS_URL, alert['lco_id'])

        return GenericAlert(
            timestamp=timestamp,
            url=url,
            id=alert['lco_id'],
            name=alert['objectId'],
            ra=alert['candidate']['ra'],
            dec=alert['candidate']['dec'],
            mag=alert['candidate']['magpsf'],
            score=alert['candidate']['rb']
        )
