from django.contrib.gis.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from openwisp_users.mixins import OrgMixin
from openwisp_utils.base import TimeStampedEditableModel


@python_2_unicode_compatible
class Location(OrgMixin, TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=75)
    address = models.CharField(_('address'), db_index=True,
                               max_length=256, blank=True)
    geometry = models.GeometryField(_('geometry'), blank=True, null=True)

    class Meta:
        unique_together = ('name', 'organization')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class FloorPlan(OrgMixin, TimeStampedEditableModel):
    location = models.ForeignKey('geo.Location')
    floor = models.SmallIntegerField(_('floor'))
    image = models.ImageField(_('image'),
                              help_text=_('floor plan image'))
    name = models.CharField(_('name'), db_index=True,
                            max_length=32, blank=True)

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
    device = models.ForeignKey('config.Device')
    type = models.CharField(choices=LOCATION_TYPES, max_length=8)
    location = models.ForeignKey('geo.Location', models.PROTECT,
                                 blank=True, null=True)
    floorplan = models.ForeignKey('geo.Floorplan', models.PROTECT,
                                  blank=True, null=True)
    # TODO: is 64 char maxlength ok?
    indoor = models.CharField(_('indoor position'), max_length=64,
                              blank=True, null=True)

    def delete(self, *args, **kwargs):
        delete_location = False
        if self.type == 'mobile':
            delete_location = True
            location = self.location
        super(DeviceLocation, self).delete(*args, **kwargs)
        if delete_location:
            location.delete()
