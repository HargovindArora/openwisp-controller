django.jQuery(function($) {
    var $outdoor = $('.geo.coords'),
        $indoor = $('.indoor.coords'),
        $allSections = $('.coords'),
        $geoRows = $('.geo.coords .form-row:not(.field-location_selection)'),
        $geoEdit = $('.field-name, .field-address, .field-geometry', '.geo.coords'),
        $geoSelection = $('.field-location', '.geo.coords'),
        geometryId = $('.geo.coords .field-geometry label').attr('for'),
        mapName = 'leafletmap' + geometryId + '-map',
        $type = $('.inline-group .field-type select'),
        $locationSelection = $('.geo.coords .field-location_selection select'),
        $location = $('select, input', '.geo.coords .field-location');

    var typeChange = function(){
        var value = $type.val();
        $allSections.hide();
        if (value == 'outdoor') {
            $outdoor.show();
        }
        else if (value == 'indoor') {
            $outdoor.show();
            $indoor.show();
        }
    }

    $type.change(typeChange);
    typeChange();

    var locationSelectionChange = function(){
        var value = $locationSelection.val();
        $geoRows.hide();
        if (value == 'new') {
            $geoEdit.show();
        }
        else if (value == 'existing') {
            $geoSelection.show();
        }
        if (window[mapName]) {
            window[mapName].invalidateSize();
        }
    }

    $locationSelection.change(locationSelectionChange);
    locationSelectionChange();

    // existing
    if ($location.val()) {
        $locationSelection.parents('.form-row').hide();
        $geoSelection.hide();
        $geoEdit.show();
    }
});
