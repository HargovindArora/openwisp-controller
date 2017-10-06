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
from .widgets import ImageWidget, FloorPlanWidget


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        exclude = tuple()

    class Media:
        js = ('geo/js/geo.js',)
        css = {'all': ('geo/css/geo.css',)}


class LocationAdmin(MultitenantAdminMixin, TimeReadonlyAdminMixin, LeafletGeoAdmin):
    list_display = ('name', 'organization', 'created', 'modified')
    list_filter = [('organization', MultitenantOrgFilter), ]
    list_select_related = ('organization',)
    search_fields = ('name', 'address')
    save_on_top = True
    form = LocationForm

    def get_urls(self):
        return [
            url(r'^(?P<pk>[^/]+)/json/$',
                self.admin_site.admin_view(self.json_view),
                name='geo_location_json')
        ] + super(LocationAdmin, self).get_urls()

    def json_view(self, request, pk):
        instance = get_object_or_404(self.model, pk=pk)
        return JsonResponse({
            'name': instance.name,
            'address': instance.address,
            'geometry': json.loads(instance.geometry.json)
        })


class FloorForm(forms.ModelForm):
    class Meta:
        model = FloorPlan
        exclude = tuple()
        widgets = {'image': ImageWidget()}

    class Media:
        css = {'all': ('geo/css/geo.css',)}


class FloorAdmin(MultitenantAdminMixin, TimeReadonlyAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'organization', 'floor', 'created', 'modified')
    list_select_related = ('location', 'organization')
    search_fields = ('location__name', 'name')
    raw_id_fields = ('location',)
    save_on_top = True
    form = FloorForm


class DeviceLocationForm(forms.ModelForm):
    CHOICES = (
        ('', _('Please select one choice')),
        ('new', _('New')),
        ('existing', _('Existing'))
    )
    location_selection = forms.ChoiceField(choices=CHOICES, required=False)
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
                             widget=ImageWidget(thumbnail=False),
                             help_text=_('floor plan image'))
    indoor = forms.CharField(max_length=64, required=False,
                             label=_('indoor position'),
                             widget=FloorPlanWidget)

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
        obj = self.instance
        location = obj.location
        floorplan = obj.floorplan
        if location:
            initial.update({
                'location_selection': 'existing',
                'name': location.name,
                'address': location.address,
                'geometry': location.geometry,
            })
        if floorplan:
            initial.update({
                'floorplan_selection': 'existing',
                'floor': floorplan.floor,
                'image': floorplan.image
            })
        self.initial.update(initial)

    def clean(self):
        data = self.cleaned_data
        type_ = data['type']
        msg = _('this field is required for locations of type %(type)s')
        if type_ in ['outdoor', 'indoor'] and not data['location']:
            for field in ['location_selection', 'name', 'address', 'geometry']:
                if field in data and not data[field]:
                    params = {'type': type_}
                    err = ValidationError(msg, params=params)
                    self.add_error(field, err)
        if type_ == 'indoor' and not data['floorplan']:
            for field in ['floorplan_selection', 'floor', 'image']:
                if field in data and not data[field]:
                    params = {'type': type_}
                    err = ValidationError(msg, params=params)
                    self.add_error(field, err)
        elif type_ == 'mobile' and not self.instance.location:
            data['name'] = self.instance.device.name
            data['address'] = ''
            data['geometry'] = ''
            data['location_selection'] = 'new'
        elif type_ == 'mobile' and self.instance.location:
            data['location_selection'] = 'existing'

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
        if data['type'] == 'indoor' and not instance.floorplan:
            instance.floorplan = FloorPlan.objects.create(
                organization=instance.device.organization,
                location=instance.location,
                floor=data['floor'],
                image=data['image']
            )
        elif data['type'] == 'indoor':
            instance.floorplan.floor = data['floor'] or instance.floorplan.floor
            instance.floorplan.image = data['image'] or instance.location.image
            instance.floorplan.save()
        # call super
        return super(DeviceLocationForm, self).save(commit=True)


class DeviceLocationInline(TimeReadonlyAdminMixin, admin.StackedInline):
    model = DeviceLocation
    form = DeviceLocationForm
    extra = 1
    max_num = 1
    verbose_name = _('geographic information')
    verbose_name_plural = verbose_name
    raw_id_fields = ('location',)
    template = 'admin/geo/location_inline.html'
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
