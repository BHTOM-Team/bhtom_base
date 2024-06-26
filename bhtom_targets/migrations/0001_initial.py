# Generated by Django 4.0.4 on 2024-03-08 15:49

import bhtom_base.bhtom_targets.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Target',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', help_text="The name of this target e.g. Barnard's star.", max_length=100, unique=True, verbose_name='Name')),
                ('type', models.CharField(choices=[('SIDEREAL', 'Sidereal'), ('NON_SIDEREAL', 'Non-sidereal')], db_index=True, help_text='The type of this target.', max_length=100, verbose_name='Target Type')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='The time which this target was created in the TOM database.', verbose_name='Time Created')),
                ('modified', models.DateTimeField(auto_now=True, help_text='The time which this target was changed in the TOM database.', verbose_name='Last Modified')),
                ('ra', models.FloatField(blank=True, db_index=True, help_text='Right Ascension, in degrees.', null=True, verbose_name='Right Ascension')),
                ('dec', models.FloatField(blank=True, db_index=True, help_text='Declination, in degrees.', null=True, verbose_name='Declination')),
                ('epoch', models.FloatField(blank=True, help_text='Julian Years. Max 2100.', null=True, verbose_name='Epoch')),
                ('parallax', models.FloatField(blank=True, help_text='Parallax, in milliarcseconds.', null=True, verbose_name='Parallax')),
                ('pm_ra', models.FloatField(blank=True, help_text='Proper Motion: RA. Milliarsec/year.', null=True, verbose_name='Proper Motion (RA)')),
                ('pm_dec', models.FloatField(blank=True, help_text='Proper Motion: Dec. Milliarsec/year.', null=True, verbose_name='Proper Motion (Declination)')),
                ('galactic_lng', models.FloatField(blank=True, db_index=True, help_text='Galactic Longitude in degrees.', null=True, verbose_name='Galactic Longitude')),
                ('galactic_lat', models.FloatField(blank=True, db_index=True, help_text='Galactic Latitude in degrees.', null=True, verbose_name='Galactic Latitude')),
                ('distance', models.FloatField(blank=True, help_text='Parsecs.', null=True, verbose_name='Distance')),
                ('distance_err', models.FloatField(blank=True, help_text='Parsecs.', null=True, verbose_name='Distance Error')),
                ('scheme', models.CharField(blank=True, choices=[('MPC_MINOR_PLANET', 'MPC Minor Planet'), ('MPC_COMET', 'MPC Comet'), ('JPL_MAJOR_PLANET', 'JPL Major Planet')], default='', max_length=50, verbose_name='Orbital Element Scheme')),
                ('epoch_of_elements', models.FloatField(blank=True, help_text='Julian date.', null=True, verbose_name='Epoch of Elements')),
                ('mean_anomaly', models.FloatField(blank=True, help_text='Angle in degrees.', null=True, verbose_name='Mean Anomaly')),
                ('arg_of_perihelion', models.FloatField(blank=True, help_text='Argument of Perhihelion. J2000. Degrees.', null=True, verbose_name='Argument of Perihelion')),
                ('eccentricity', models.FloatField(blank=True, help_text='Eccentricity', null=True, verbose_name='Eccentricity')),
                ('lng_asc_node', models.FloatField(blank=True, help_text='Longitude of Ascending Node. J2000. Degrees.', null=True, verbose_name='Longitude of Ascending Node')),
                ('inclination', models.FloatField(blank=True, help_text='Inclination to the ecliptic. J2000. Degrees.', null=True, verbose_name='Inclination to the ecliptic')),
                ('mean_daily_motion', models.FloatField(blank=True, help_text='Degrees per day.', null=True, verbose_name='Mean Daily Motion')),
                ('semimajor_axis', models.FloatField(blank=True, help_text='In AU', null=True, verbose_name='Semimajor Axis')),
                ('epoch_of_perihelion', models.FloatField(blank=True, help_text='Julian Date.', null=True, verbose_name='Epoch of Perihelion')),
                ('ephemeris_period', models.FloatField(blank=True, help_text='Days', null=True, verbose_name='Ephemeris Period')),
                ('ephemeris_period_err', models.FloatField(blank=True, help_text='Days', null=True, verbose_name='Ephemeris Period Error')),
                ('ephemeris_epoch', models.FloatField(blank=True, help_text='Days', null=True, verbose_name='Ephemeris Epoch')),
                ('ephemeris_epoch_err', models.FloatField(blank=True, help_text='Days', null=True, verbose_name='Ephemeris Epoch Error')),
                ('perihdist', models.FloatField(blank=True, help_text='AU', null=True, verbose_name='Perihelion Distance')),
                ('classification', models.CharField(blank=True, choices=[('Unknown', 'Unknown'), ('Be-star outburst', 'Be-star outburst'), ('AGN', 'Active Galactic Nucleus(AGN)'), ('BL Lac', 'BL Lac'), ('CV', 'Cataclysmic Variable(CV)'), ('CEPH', 'Cepheid Variable(CEPH)'), ('EB', 'Eclipsing Binary(EB)'), ('Galaxy', 'Galaxy'), ('LPV', 'Long Period Variable(LPV)'), ('LBV', 'Luminous Blue Variable(LBV)'), ('M-dwarf flare', 'M-dwarf flare'), ('Microlensing Event', 'Microlensing Event'), ('Nova', 'Nova'), ('Peculiar Supernova', 'Peculiar Supernova'), ('QSO', 'Quasar(QSO)'), ('RCrB', 'R CrB Variable'), ('RR Lyrae Variable', 'RR Lyrae Variable'), ('SSO', 'Solar System Object(SSO)'), ('Star', 'Star'), ('SN', 'Supernova(SN)'), ('Supernova imposter', 'Supernova imposter'), ('Symbiotic star', 'Symbiotic star'), ('TDE', 'Tidal Disruption Event(TDE)'), ('Variable star-other', 'Variable star-other'), ('XRB', 'X-Ray Binary(XRB)'), ('YSO', 'Young Stellar Object(YSO)')], db_index=True, help_text='Classification of the object (e.g. variable star, microlensing event)', max_length=50, null=True, verbose_name='classification')),
                ('discovery_date', models.DateTimeField(blank=True, help_text='Date of the discovery, YYYY-MM-DDTHH:MM:SS, or leave blank', null=True, verbose_name='discovery date')),
                ('mjd_last', models.FloatField(blank=True, default=0, null=True, verbose_name='mjd last')),
                ('mag_last', models.FloatField(blank=True, db_index=True, default=100, null=True, verbose_name='mag last')),
                ('importance', models.FloatField(db_index=True, default=0, help_text='Target importance as an integer 0-10 (10 is the highest)', verbose_name='importance')),
                ('cadence', models.FloatField(default=0, help_text='Requested cadence (0-100 days)', verbose_name='cadence')),
                ('priority', models.FloatField(blank=True, db_index=True, default=0, null=True, verbose_name='priority')),
                ('sun_separation', models.FloatField(blank=True, db_index=True, null=True, verbose_name='sun separation')),
                ('creation_date', models.DateTimeField(blank=True, null=True, verbose_name='creation date')),
                ('constellation', models.CharField(blank=True, max_length=50, null=True, verbose_name='constellation')),
                ('dont_update_me', models.BooleanField(blank=True, null=True, verbose_name='dont update_me')),
                ('phot_class', models.CharField(blank=True, max_length=50, null=True, verbose_name='phot class')),
                ('photometry_plot', models.FileField(blank=True, default=None, null=True, upload_to=bhtom_base.bhtom_targets.models.Target.photometry_plot_path)),
                ('photometry_plot_obs', models.FileField(blank=True, default=None, null=True, upload_to=bhtom_base.bhtom_targets.models.Target.photometry_plot_obs_path)),
                ('photometry_icon_plot', models.FileField(blank=True, default=None, null=True, upload_to=bhtom_base.bhtom_targets.models.Target.photometry_icon_plot_path)),
                ('spectroscopy_plot', models.FileField(blank=True, default=None, null=True, upload_to=bhtom_base.bhtom_targets.models.Target.spectroscopy_plot_path)),
                ('data_plot', models.DateTimeField(blank=True, null=True, verbose_name='creation plot date')),
                ('filter_last', models.CharField(blank=True, default='', max_length=20, null=True, verbose_name='last filter')),
                ('cadence_priority', models.FloatField(blank=True, default=0, null=True, verbose_name='cadence priority')),
                ('description', models.CharField(blank=True, db_index=True, max_length=200, null=True, verbose_name='description')),
            ],
        ),
        migrations.CreateModel(
            name='TargetList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the target list.', max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True, help_text='The time which this target list was created in the TOM database.')),
                ('modified', models.DateTimeField(auto_now=True, help_text='The time which this target list was changed in the TOM database.', verbose_name='Last Modified')),
                ('targets', models.ManyToManyField(to='bhtom_targets.target')),
            ],
            options={
                'ordering': ('-created', 'name'),
            },
        ),
        migrations.CreateModel(
            name='TargetGaiaDr3',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_id', models.BigIntegerField(db_index=True, unique=True, verbose_name='Source Id')),
                ('parallax', models.FloatField(blank=True, null=True, verbose_name='Parallax')),
                ('parallax_error', models.FloatField(blank=True, null=True, verbose_name='Parallax Error')),
                ('pmra', models.FloatField(blank=True, null=True, verbose_name='pmra')),
                ('pmra_error', models.FloatField(blank=True, null=True, verbose_name='pmra Error')),
                ('pmdec', models.FloatField(blank=True, null=True, verbose_name='pmdec')),
                ('pmdec_error', models.FloatField(blank=True, null=True, verbose_name='pmdec Error')),
                ('ruwe', models.FloatField(blank=True, null=True, verbose_name='ruwe')),
                ('astrometric_excess_noise', models.FloatField(blank=True, null=True, verbose_name='Astrometric Excess Noise')),
                ('r_med_geo', models.FloatField(blank=True, null=True, verbose_name='r_med_geo')),
                ('r_lo_geo', models.FloatField(blank=True, null=True, verbose_name='r_lo_geo')),
                ('r_hi_geo', models.FloatField(blank=True, null=True, verbose_name='r_hi_geo')),
                ('r_med_photogeo', models.FloatField(blank=True, null=True, verbose_name='r_med_photogeo')),
                ('r_lo_photogeo', models.FloatField(blank=True, null=True, verbose_name='r_lo_photogeo')),
                ('r_hi_photogeo', models.FloatField(blank=True, null=True, verbose_name='r_hi_photogeo')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='The time which this target name was created.')),
                ('modified', models.DateTimeField(auto_now=True, help_text='The time which this target GaiaDr3 was changed in the TOM database.', verbose_name='Last Modified')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dr3', to='bhtom_targets.target')),
            ],
        ),
        migrations.CreateModel(
            name='TargetGaiaDr2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_id', models.BigIntegerField(db_index=True, unique=True, verbose_name='Source Id')),
                ('parallax', models.FloatField(blank=True, null=True, verbose_name='Parallax')),
                ('parallax_error', models.FloatField(blank=True, null=True, verbose_name='Parallax Error')),
                ('pmra', models.FloatField(blank=True, null=True, verbose_name='pmra')),
                ('pmra_error', models.FloatField(blank=True, null=True, verbose_name='pmra Error')),
                ('pmdec', models.FloatField(blank=True, null=True, verbose_name='pmdec')),
                ('pmdec_error', models.FloatField(blank=True, null=True, verbose_name='pmdec Error')),
                ('ruwe', models.FloatField(blank=True, null=True, verbose_name='ruwe')),
                ('astrometric_excess_noise', models.FloatField(blank=True, null=True, verbose_name='Astrometric Excess Noise')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='The time which this target name was created.')),
                ('modified', models.DateTimeField(auto_now=True, help_text='The time which this target GaiaDr3 was changed in the TOM database.', verbose_name='Last Modified')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dr2', to='bhtom_targets.target')),
            ],
        ),
        migrations.CreateModel(
            name='TargetName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_name', models.CharField(choices=[('GAIA_ALERTS', 'Gaia Alerts name'), ('CPCS', 'CPCS name'), ('ASASSN', 'ASASSN name'), ('OGLE_EWS', 'OGLE-EWS name'), ('ZTF', 'ZTF name'), ('ATLAS', 'ATLAS name'), ('AAVSO', 'AAVSO name'), ('TNS', 'TNS name'), ('ANTARES', 'ANTARES name'), ('ZTF_DR8', 'ZTF DR8 name'), ('SDSS', 'SDSS name'), ('NEOWISE', 'NEOWISE name'), ('ALLWISE', 'ALLWISE name'), ('CRTS', 'CRTS name'), ('LINEAR', 'LINEAR name'), ('FIRST', 'FIRST name'), ('PS1', 'PS1 name'), ('DECAPS', 'DECAPS name'), ('GAIA_DR3', 'Gaia DR3 name'), ('GAIA_DR2', 'Gaia DR2 name'), ('KMT_NET', 'KMT-NET name'), ('LOFAR', 'LOFAR2m name'), ('twomass', '2MASS name'), ('PTF', 'PTF name')], max_length=100, verbose_name='Source Name')),
                ('name', models.CharField(max_length=100, verbose_name='Alias')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='The time which this target name was created.')),
                ('modified', models.DateTimeField(auto_now=True, help_text='The time which this target name was changed in the TOM database.', verbose_name='Last Modified')),
                ('url', models.CharField(blank=True, max_length=250, null=True)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='bhtom_targets.target')),
            ],
            options={
                'unique_together': {('source_name', 'target')},
            },
        ),
        migrations.CreateModel(
            name='TargetExtra',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200)),
                ('value', models.TextField(blank=True, default='')),
                ('float_value', models.FloatField(blank=True, null=True)),
                ('bool_value', models.BooleanField(blank=True, null=True)),
                ('time_value', models.DateTimeField(blank=True, null=True)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bhtom_targets.target')),
            ],
            options={
                'unique_together': {('target', 'key')},
            },
        ),
    ]
