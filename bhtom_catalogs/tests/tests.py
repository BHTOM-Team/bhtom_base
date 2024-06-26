from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse

from bhtom_base.bhtom_catalogs.harvester import AbstractHarvester, get_service_classes, MissingDataException


class TestHarvester(AbstractHarvester):
    name = 'TEST'

    def query(self, term):
        if term == 'notfound':
            raise MissingDataException
        self.catalog_data = {'ra': 24, 'dec': 77, 'name': 'faketarget', 'type': 'SIDEREAL'}

    def to_target(self):
        target = super().to_target()
        target.name = self.catalog_data['name']
        target.type = self.catalog_data['type']
        target.ra = self.catalog_data['ra']
        target.dec = self.catalog_data['dec']
        return target


@override_settings(TOM_HARVESTER_CLASSES=['bhtom_base.bhtom_catalogs.tests.tests.TestHarvester'])
class TestHarvesterClass(TestCase):
    def test_get_broker_class(self):
        self.assertIn(TestHarvester, get_service_classes().values())


@override_settings(TOM_HARVESTER_CLASSES=['bhtom_base.bhtom_catalogs.tests.tests.TestHarvester'])
class TestHarvesterViews(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='test', password='test')
        self.client.force_login(user)

    def test_service_available(self):
        response = self.client.get(reverse('bhtom_base.bhtom_catalogs:query'))
        self.assertContains(response, TestHarvester.name)

    def test_do_search(self):
        data = {'term': 'atarget', 'service': 'TEST'}
        response = self.client.post(reverse('bhtom_base.bhtom_catalogs:query'), data=data, follow=True)
        self.assertContains(response, 'faketarget')


# TODO: investigate
    # def test_not_found(self):
    #     data = {'term': 'notfound', 'service': 'TEST'}
    #     response = self.client.post(reverse('bhtom_base.bhtom_catalogs:query'), data=data, follow=True)
    #     self.assertContains(response, 'Object not found')
