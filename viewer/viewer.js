/* global L, jQuery, noUiSlider */

let $ = (selector, scope = document) => {
    return scope.querySelector(selector);
};

let $$ = (selector, scope = document) => {
    return Array.from(scope.querySelectorAll(selector));
};

function removeChildren(element) {
    while (element.firstChild) {
        element.firstChild.remove();
    }
}

let allPoints,
    allItems,
    startYear = 1860,
    endYear = 2018;

let stadiumIcon = L.icon({
    iconUrl: "static/icons/stadium.svg",
    iconSize: [32, 32],
    iconAnchor: [12, 12],
    popupAnchor: [0, 0]
});

let baseballCapIcon = L.icon({
    iconUrl: "static/icons/baseball_cap.svg",
    iconSize: [26, 17],
    iconAnchor: [13, 18],
    popupAnchor: [0, 0]
});

let map = L.map("viewer-map", {
    zoom: 3
});

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

let placeLayer = L.featureGroup().addTo(map);
let allPlaceMarkers = [];

fetch("InsideBaseball.json")
    .then(response => {
        return response.json();
    })
    .then(data => {
        allPoints = data.points;
        allItems = data.items;

        allPoints.forEach(point => {
            let title = point.title || JSON.stringify(point.latlng);

            let marker = L.marker(point.latlng, {
                title: title,
                items: point.items
            });

            marker.bindPopup(title);
            marker.on("click", function(evt) {
                displayItems(evt.target.options.items);
                applyVisibilityFilters();
            });

            marker.addTo(placeLayer);
            allPlaceMarkers.push(marker);
        });

        Object.values(allItems).forEach(v => {
            let searchText = [v.title];
            for (let value of Object.values(v.metadata)) {
                if (Array.isArray(value)) {
                    value.forEach(val => searchText.push(val));
                } else {
                    searchText.push(value);
                }
            }
            v.searchText = searchText.join("\n").toLocaleLowerCase();
        });

        displayAllItems();
    });

let layerControl = L.control.layers(null).addTo(map);

fetch(
    "https://raw.githubusercontent.com/cageyjames/GeoJSON-Ballparks/master/ballparks.geojson"
)
    .then(response => {
        return response.json();
    })
    .then(data => {
        let ballparksLayer = L.geoJSON(data, {
            pointToLayer: (feature, latlng) => {
                let props = feature.properties,
                    title = `${props.Ballpark} (${props.Team})`;

                return L.marker(latlng, {
                    icon: stadiumIcon,
                    title: title
                });
            }
        });

        layerControl.addOverlay(ballparksLayer, "Present Day Ballparks");
    });

fetch("teams.geojson")
    .then(response => {
        return response.json();
    })
    .then(data => {
        let ballparksLayer = L.geoJSON(data, {
            pointToLayer: (feature, latlng) => {
                let props = feature.properties,
                    title = props.Teams || props.Stadiums || props.Leagues;

                return L.marker(latlng, {
                    icon: baseballCapIcon,
                    title: title
                });
            }
        });

        layerControl.addOverlay(ballparksLayer, "Teams");
    });

map.setView({ lat: 38.8879105, lng: -77.0024652 }, 7);

let itemListing = $("#viewer-items > ul");

function displayItems(itemIDs) {
    removeChildren(itemListing);

    itemIDs.forEach(itemID => {
        let item = allItems[itemID];
        // Convenience aliases
        let title = item.title;
        let meta = item.metadata;

        let itemContainer = document.createElement("li");
        itemContainer.classList.add("list-group-item", "item-listing");
        itemContainer.id = "item-" + itemID;
        itemContainer.dataset.itemID = itemID;
        itemListing.appendChild(itemContainer);

        let itemLink = document.createElement("a");
        itemLink.textContent = title;
        itemLink.href = meta["Digital ID URL"];
        itemLink.target = "_blank";

        itemLink.addEventListener("click", evt => {
            updateItemPreview(item);
            jQuery("#viewer-item-preview").modal();
            evt.preventDefault();
            evt.stopPropagation();
            return false;
        });

        itemContainer.appendChild(itemLink);
    });
}

function displayAllItems() {
    displayItems(Object.values(allItems).map(v => v.id));
}

map.on("click", () => {
    displayAllItems();
    applyVisibilityFilters();
});

function updateItemPreview(item) {
    let preview = $("#viewer-item-preview");
    $$(".title", preview).forEach(elem => (elem.textContent = item.title));
    $(".description", preview).textContent = item.metadata.Description;

    $("img", preview).src = item.imageLarge;

    $$("a", preview).forEach(link => (link.href = item.metadata["Digital ID URL"]));

    let tbody = $(".metadata-table tbody", preview);
    removeChildren(tbody);

    for (let [field, value] of Object.entries(item.metadata)) {
        if (field == "Description" || !value || value.length < 1) {
            continue;
        }

        let row = document.createElement("tr");

        let th = document.createElement("th");
        th.scope = "row";
        th.textContent = field;
        row.appendChild(th);

        let td = document.createElement("td");
        td.textContent = value;
        row.appendChild(td);

        tbody.appendChild(row);
    }
}

function getVisibleItems() {
    // Apply search text filters:
    let searchText = textSearchInput.value.trim().toLocaleLowerCase();

    let visibleItems = Object.values(allItems)
        .filter(item => item.searchText.indexOf(searchText) > -1)
        .filter(item => item.startYear >= startYear && item.endYear <= endYear)
        .map(item => item.id);

    return visibleItems;
}

function applyVisibilityFilters() {
    if (!allItems) {
        return;
    }

    let visibleItemIDs = getVisibleItems();

    $$(".item-listing", itemListing).forEach(node => {
        node.classList.toggle(
            "hidden",
            visibleItemIDs.indexOf(node.dataset.itemID) < 0
        );
    });

    applyMapVisibilityFilter(visibleItemIDs);
}

function applyMapVisibilityFilter(visibleItemIDs) {
    // Iterate over the points to see which one has at least one visible item

    let visibleIDSet = new Set(visibleItemIDs);

    allPlaceMarkers.forEach(marker => {
        let isVisible =
            marker.options.items.filter(i => visibleIDSet.has(i)).length > 0;

        if (isVisible) {
            placeLayer.addLayer(marker);
        } else {
            placeLayer.removeLayer(marker);
        }
    });
}

//     map.fitBounds(placeLayer.getBounds(), { animate: true });

let textSearchInput = $("#item-text-search");
textSearchInput.addEventListener("input", () => {
    applyVisibilityFilters();
});

function createSlider(element) {
    noUiSlider.create(element, {
        start: [startYear, endYear],
        range: {
            min: startYear,
            max: endYear
        },
        format: {
            to: function(value) {
                return value.toFixed(0);
            },
            from: function(value) {
                return parseInt(value, 10);
            }
        },
        pips: {
            mode: "count",
            values: 6,
            density: 10
        },
        behaviour: "drag",
        connect: true
    });

    let labels = [
        element.querySelector('.noUi-handle[data-handle="0"]'),
        element.querySelector('.noUi-handle[data-handle="1"]')
    ];

    element.noUiSlider.on("update", (values, handle) => {
        labels[handle].innerText = values[handle];

        startYear = Math.floor(parseInt(values[0], 10) - 1);
        endYear = Math.ceil(parseInt(values[1], 10) + 1);

        applyVisibilityFilters();
    });
}

createSlider($("#slider"));
