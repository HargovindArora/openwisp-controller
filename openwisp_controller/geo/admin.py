import json

from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from leaflet.admin import LeafletGeoAdmin

from openwisp_utils.admin import MultitenantOrgFilter, TimeReadonlyAdminMixin

from ..admin import MultitenantAdminMixin
from ..config.admin import DeviceAdmin as BaseDeviceAdmin
from ..config.admin import ConfigInline
from ..config.models import Device
from .fields import GeometryField
from .models import DeviceLocation, FloorPlan, Location
from .widgets import ImageWidget


class LocationAdmin(MultitenantAdminMixin, TimeReadonlyAdminMixin, LeafletGeoAdmin):
    list_display = ('name', 'created', 'modified')
    list_filter = [('organization', MultitenantOrgFilter), ]
    list_select_related = ('organization',)

    def get_urls(self):
        return [
            url(r'^(?P<pk>[^/]+)/json/$',
                self.admin_site.admin_view(self.json_view),
                name='geo_location_json')
        ] + super(LocationAdmin, self).get_urls()

    def json_view(self, request, pk):
        instance = get_object_or_404(self.model, pk=pk)
        return JsonResponse({
            "name": instance.name,
            "address": instance.address,
            "geometry": json.loads(instance.geometry.json)
        })


class FloorForm(forms.ModelForm):
    class Meta:
        model = FloorPlan
        exclude = tuple()
        widgets = {'image': ImageWidget()}


class FloorAdmin(TimeReadonlyAdminMixin, admin.ModelAdmin):
    list_display = ('location', 'floor', 'name', 'created', 'modified')
    list_select_related = ('location',)
    search_fields = ('location__name', 'name')
    form = FloorForm


class DeviceLocationForm(forms.ModelForm):
    CHOICES = (
        ('', _('Please select one choice')),
        ('new', _('New')),
        ('existing', _('Existing'))
    )
    location_selection = forms.ChoiceField(required=True,
                                           choices=CHOICES)
    name = forms.CharField(label=_('Location name'),
                           max_length=75, required=False,
                           help_text=_('Descriptive name of the location '
                                       '(building name, company name, etc.)'))
    address = forms.CharField(max_length=128, required=False)
    geometry = GeometryField(required=False)
    floorplan_selection = forms.ChoiceField(required=False,
                                            choices=CHOICES)
    floor = forms.IntegerField(required=False)
    image = forms.ImageField(required=False,
                             help_text=_('floor plan image'))

    class Meta:
        model = DeviceLocation
        exclude = tuple()

    class Media:
        js = ('geo/js/geo.js',)
        css = {'all': ('geo/css/geo.css',)}

    def __init__(self, *args, **kwargs):
        super(DeviceLocationForm, self).__init__(*args, **kwargs)
        # set initial values for custom fields
        initial = {}
        location = self.instance.location
        if location:
            initial.update({
                'location_selection': 'existing',
                'name': location.name,
                'address': location.address,
                'geometry': location.geometry,
            })
        self.initial.update(initial)

    def clean(self):
        data = self.cleaned_data
        type_ = data['type']
        msg = _('%(field)s is required for locations of type %(type)s')
        if type_ in ['outdoor', 'indoor'] and not data['location']:
            for field in ['name', 'address', 'geometry']:
                if not self.cleaned_data[field]:
                    params = {'field': field, 'type': type_}
                    err = ValidationError(msg, params=params)
                    self.add_error(field, err)

    def save(self, commit=True):
        instance = self.instance
        data = self.cleaned_data
        # create or update location
        if not instance.location:
            instance.location = Location.objects.create(
                organization=instance.device.organization,
                name=data['name'],
                address=data['address'],
                geometry=data['geometry'],
            )
        else:
            instance.location.name = data['name'] or instance.location.name
            instance.location.address = data['address'] or instance.location.address
            instance.location.geometry = data['geometry'] or instance.location.geometry
            instance.location.save()
        # call super
        return super(DeviceLocationForm, self).save(commit=True)


class DeviceLocationInline(TimeReadonlyAdminMixin, admin.StackedInline):
    model = DeviceLocation
    form = DeviceLocationForm
    extra = 1
    verbose_name = _('geographic information')
    verbose_name_plural = verbose_name
    raw_id_fields = ('location',)
    template = 'geo/admin/location_inline.html'
    fieldsets = (
        (None, {'fields': ('type',)}),
        ('Geographic coordinates', {
            'classes': ('geo', 'coords'),
            'fields': ('location_selection', 'location',
                       'name', 'address', 'geometry'),
        }),
        ('Indoor coordinates', {
            'classes': ('indoor', 'coords'),
            'fields': ('floorplan_selection', 'floorplan',
                       'floor', 'image', 'indoor',),
        })
    )


class DeviceAdmin(BaseDeviceAdmin):
    inlines = [DeviceLocationInline, ConfigInline]


admin.site.register(Location, LocationAdmin)
admin.site.register(FloorPlan, FloorAdmin)
admin.site.unregister(Device)
admin.site.register(Device, DeviceAdmin)
