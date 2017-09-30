django.jQuery(function($) {
    var $outdoor = $('.geo.coords'),
        $indoor = $('.indoor.coords'),
        $allSections = $('.coords'),
        $geoRows = $('.geo.coords .form-row:not(.field-location_selection)'),
        $geoEdit = $('.field-name, .field-address, .field-geometry', '.geo.coords'),
        $geoSelection = $('.field-location', '.geo.coords'),
        geometryId = $('.geo.coords .field-geometry label').attr('for'),
        mapName = 'leafletmap' + geometryId + '-map',
        loadMapName = 'loadmap' + geometryId + '-map',
        $type = $('.inline-group .field-type select'),
        $locationSelection = $('.geo.coords .field-location_selection select'),
        $location = $('select, input', '.geo.coords .field-location'),
        baseLocationJsonUrl = $('#geo-location-json-url').attr('data-url');

    function getLocationJsonUrl(pk) {
        return baseLocationJsonUrl.replace('0000', pk)
    }

    function getMap() {
        return window[mapName];
    }

    function invalidateMapSize() {
        var map = getMap();
        if (map) { map.invalidateSize() }
        return map;
    }

    function typeChange() {
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

    function locationSelectionChange() {
        var value = $locationSelection.val();
        $geoRows.hide();
        if (value == 'new') {
            $geoEdit.show();
        }
        else if (value == 'existing') {
            $geoSelection.show();
        }
        invalidateMapSize();
    }

    // HACK to override `dismissRelatedLookupPopup()` and
    // `dismissAddAnotherPopup()` in Django's RelatedObjectLookups.js to
    // trigger change event when an ID is selected or added via popup.
    function triggerChangeOnField(win, chosenId) {
        $(document.getElementById(windowname_to_id(win.name))).change();
    }
    window.ORIGINAL_dismissRelatedLookupPopup = window.dismissRelatedLookupPopup
    window.dismissRelatedLookupPopup = function(win, chosenId) {
        ORIGINAL_dismissRelatedLookupPopup(win, chosenId);
        triggerChangeOnField(win, chosenId);
    }
    window.ORIGINAL_dismissAddAnotherPopup = window.dismissAddAnotherPopup
    window.dismissAddAnotherPopup = function(win, chosenId) {
        ORIGINAL_dismissAddAnotherPopup(win, chosenId);
        triggerChangeOnField(win, chosenId);
    }

    $type.change(typeChange);
    typeChange();

    $locationSelection.change(locationSelectionChange);
    locationSelectionChange();

    $location.change(function(){
        var url = getLocationJsonUrl($location.val());
        $.getJSON(url, function(data){
            $('.field-name input', '.geo.coords').val(data.name);
            $('.field-address input', '.geo.coords').val(data.address);
            $('.field-geometry textarea', '.geo.coords').val(JSON.stringify(data.geometry));
            getMap().remove();
            $geoEdit.show();
            window[loadMapName]();
        });
    });

    // show existing location
    if ($location.val()) {
        $locationSelection.parents('.form-row').hide();
        $geoSelection.hide();
        $geoEdit.show();
    }
});
