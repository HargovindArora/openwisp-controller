from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.utils.html import mark_safe

from leaflet.forms.widgets import LeafletWidget as BaseLeafletWidget


class ImageWidget(forms.FileInput):
    """
    A ImageField Widget that shows a thumbnail.
    """
    def render(self, name, value, attrs=None):
        output = [super(ImageWidget, self).render(name, value, attrs)]
        if value and hasattr(value, 'url'):
            output.append(('<br/><br/><a rel="facebox" target="_blank" href="%s">'
                           '<img style="width:300px;margin-left: 170px;" class="floorplan" src="%s" /></a><br/>'
                           % (value.url, value.url)))
        return mark_safe(u''.join(output))


class LeafletWidget(BaseLeafletWidget):
    include_media = True
    geom_type = 'GEOMETRY'
    template_name = 'leaflet/admin/widget.html'
    modifiable = True
    map_width = '100%'
    map_height = '400px'
    display_raw = False
    settings_overrides = {}


# class FloorPlanWidget(forms.TextInput):
#     template_name = 'geo/forms/widgets/floorplan.html'
#
#     @property
#     def media(self):
#         prefix = 'geo'
#         js = [static('{0}/js/{1}'.format(prefix, f))
#               for f in ('lib/leaflet.js',
#                         'floorplan-widget.js')]
#         css = {'all': (static('{0}/css/{1}'.format(prefix, f))
#                        for f in ('lib/leaflet.css',
#                                  'floorplan-widget.css'))}
#         return forms.Media(js=js, css=css)
