/*
this JS is shared between:
    - DeviceLocationForm
    - LocationForm
*/
django.jQuery(function($) {
    var $outdoor = $('.geo.coords'),
        $indoor = $('.indoor.coords'),
        $allSections = $('.coords'),
        $geoRows = $('.geo.coords .form-row:not(.field-location_selection)'),
        $geoEdit = $('.field-name, .field-address, .field-geometry', '.geo.coords'),
        $geoSelection = $('.field-location', '.geo.coords'),
        geometryId = $('.field-geometry label').attr('for'),
        mapName = 'leafletmap' + geometryId + '-map',
        loadMapName = 'loadmap' + geometryId + '-map',
        $type = $('.inline-group .field-type select'),
        $locationSelection = $('.geo.coords .field-location_selection select'),
        $locationSelectionRow = $locationSelection.parents('.form-row'),
        $location = $('select, input', '.field-location'),
        $locationLabel = $('.field-location .item-label'),
        $name = $('.field-name input', '.geo.coords'),
        $address = $('.field-address input', '.geo.coords'),
        $geometryTextarea = $('.field-geometry textarea'),
        baseLocationJsonUrl = $('#geo-location-json-url').attr('data-url'),
        $geometryRow = $geometryTextarea.parents('.form-row'),
        msg = gettext('Location data not received yet'),
        $noLocationDiv = $('.no-location', '.geo.coords');

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

    function resetDeviceLocationForm(keepLocationSelection) {
        $locationSelectionRow.show();
        if (!keepLocationSelection) {
            $locationSelection.val('');
        }
        $location.val('');
        $locationLabel.text('');
        $name.val('');
        $address.val('');
        $geometryTextarea.val('');
        $geoEdit.hide();
        $geoSelection.hide();
        $locationSelection.show();
        $noLocationDiv.hide();
    }

    function typeChange(e, initial) {
        var value = $type.val();
        $allSections.hide();
        if (!initial) {
            resetDeviceLocationForm();
        }
        if (value == 'outdoor') {
            $outdoor.show();
        }
        else if (value == 'indoor') {
            $outdoor.show();
            $indoor.show();
        }
    }

    function locationSelectionChange(e, initial) {
        var value = $locationSelection.val();
        $geoRows.hide();
        if (!initial) {
            resetDeviceLocationForm(true);
        }
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
    typeChange(null, true);

    $locationSelection.change(locationSelectionChange);
    locationSelectionChange(null, true);

    $location.change(function(){
        var url = getLocationJsonUrl($location.val());
        $.getJSON(url, function(data){
            $locationLabel.text(data.name);
            $name.val(data.name);
            $address.val(data.address);
            $geometryTextarea.val(JSON.stringify(data.geometry));
            getMap().remove();
            $geoEdit.show();
            window[loadMapName]();
        });
    });

    // websocket for mobile coords
    function listenForLocationUpdates(pk) {
        ws = new WebSocket('ws://' + window.location.host + '/geo/mobile-location/' + pk + '/');
        ws.onmessage = function(e) {
            $geometryRow.show();
            $noLocationDiv.hide();
            $geometryTextarea.val(e.data);
            getMap().remove();
            window[loadMapName]();
        }
    }

    // show existing location
    if ($location.val()) {
        $locationSelectionRow.hide();
        $geoSelection.hide();
        $geoEdit.show();
    }
    // show mobile map (hide not relevant fields)
    if($type.val() == 'mobile') {
        $outdoor.show();
        $locationSelection.parents('.form-row').hide();
        $geoSelection.hide();
        $name.parents('.form-row').hide();
        $address.parents('.form-row').hide();
        // if no location data yet
        if (!$geometryTextarea.val()) {
            $geometryRow.hide()
            $geometryRow.parent().append('<div class="no-location">' + msg + '</div>');
            $noLocationDiv = $('.no-location', '.geo.coords');
        }
        listenForLocationUpdates($location.val());
    }
    else if(!$type.length){
        var pk = window.location.pathname.split('/').slice('-3', '-2')[0];
        listenForLocationUpdates(pk);
    }
});
