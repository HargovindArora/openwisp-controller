from django.apps import AppConfig


class GeoConfig(AppConfig):
    name = 'openwisp_controller.geo'
    label = 'geo'

    def ready(self):
        import leaflet
        leaflet.app_settings['NO_GLOBALS'] = False
        from .channels import receivers  # noqa
