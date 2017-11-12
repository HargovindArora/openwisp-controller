from django.contrib.gis.db import models
from django.contrib.humanize.templatetags.humanize import ordinal
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from openwisp_users.mixins import OrgMixin, ValidateOrgMixin
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

    class Meta:
        unique_together = ('location', 'floor')

    def __str__(self):
        return '{0} {1} {2}'.format(self.location.name,
                                    ordinal(self.floor),
                                    _('floor'))

    def clean(self):
        self._validate_org_relation('location')

    def save(self, *args, **kwargs):
        return super(FloorPlan, self).save(*args, **kwargs)


@python_2_unicode_compatible
class DeviceLocation(ValidateOrgMixin, TimeStampedEditableModel):
    LOCATION_TYPES = (
        ('outdoor', _('Outdoor')),
        ('indoor', _('Indoor')),
        ('mobile', _('Mobile')),
    )
    device = models.OneToOneField('config.Device')
    type = models.CharField(choices=LOCATION_TYPES, max_length=8)
    location = models.ForeignKey('geo.Location', models.PROTECT,
                                 blank=True, null=True)
    floorplan = models.ForeignKey('geo.Floorplan', models.PROTECT,
                                  blank=True, null=True)
    indoor = models.CharField(_('indoor position'), max_length=64,
                              blank=True, null=True)

    def _clean_location(self):
        if self.type == 'indoor' and self.location != self.floorplan.location:
            raise ValidationError(_('Invalid floorplan (belongs to a different location)'))

    def clean(self):
        self._validate_org_relation('location', field_error='location')
        if self.floorplan:
            self._validate_org_relation('floorplan', field_error='floorplan')
        self._clean_location()

    def delete(self, *args, **kwargs):
        delete_location = False
        if self.type == 'mobile':
            delete_location = True
            location = self.location
        super(DeviceLocation, self).delete(*args, **kwargs)
        if delete_location:
            location.delete()

    @property
    def organization_id(self):
        return self.device.organization_id
