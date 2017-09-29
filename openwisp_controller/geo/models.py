import uuid

from django.contrib.gis.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from openwisp_utils.base import TimeStampedEditableModel
from openwisp_users.mixins import OrgMixin


# TODO: is shareable good?
@python_2_unicode_compatible
class Location(OrgMixin, TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=75, unique=True)
    address = models.CharField(_('address'), max_length=128, blank=True)
    geometry = models.GeometryField(_('geometry'))

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class FloorPlan(OrgMixin, TimeStampedEditableModel):
    location = models.ForeignKey('geo.Location')
    floor = models.SmallIntegerField(_('floor'))
    image = models.ImageField(_('image'),
                              help_text=_('floor plan image'))
    name = models.CharField(_('name'), max_length=32, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        return _('Floor {0} - {1}').format(self.floor, self.location.name)

    def clean(self):
        self._validate_org_relation('location')


@python_2_unicode_compatible
class DeviceLocation(TimeStampedEditableModel):
    LOCATION_TYPES = (
        ('outdoor', _('Outdoor')),
        ('indoor', _('Indoor')),
        ('mobile', _('Mobile')),
    )
    device = models.OneToOneField('config.Device')
    type = models.CharField(choices=LOCATION_TYPES, max_length=8)
    location = models.ForeignKey('geo.Location', blank=True, null=True)
    floorplan = models.ForeignKey('geo.Floorplan', blank=True, null=True)
    # TODO: is 64 char maxlength ok?
    indoor = models.CharField(_('indoor position'), max_length=64,
                              blank=True, null=True)
