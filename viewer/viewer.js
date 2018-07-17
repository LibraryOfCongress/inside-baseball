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

class ItemViewer {
    constructor() {
        this.startYear = 1860;
        this.endYear = 2018;

        this.itemListing = $("#viewer-items > ul");

        this.loadData();
        this.loadBallparkLayer();
        this.loadTeamLayer();
        this.setupTextSearch();
        this.setupMap();
        this.setupTimeline();
    }

    setupMap() {
        this.stadiumIcon = L.icon({
            iconUrl: "static/icons/stadium.svg",
            iconSize: [32, 32],
            iconAnchor: [12, 12],
            popupAnchor: [0, 0]
        });

        this.baseballCapIcon = L.icon({
            iconUrl: "static/icons/baseball_cap.svg",
            iconSize: [26, 17],
            iconAnchor: [13, 18],
            popupAnchor: [0, 0]
        });

        let map = L.map("viewer-map", {
            zoom: 3
        });
        this.map = map;

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);

        this.placeLayer = L.featureGroup().addTo(map);
        this.allPlaceMarkers = [];
        this.layerControl = L.control.layers(null).addTo(map);

        map.setView({ lat: 38.8879105, lng: -77.0024652 }, 7);

        map.on("click", () => {
            this.displayAllItems();
            this.applyVisibilityFilters();
        });
    }

    loadData() {
        fetch("InsideBaseball.json")
            .then(response => {
                return response.json();
            })
            .then(data => {
                this.allPoints = data.points;
                this.allItems = data.items;

                this.allPoints.forEach(point => {
                    let title = point.title || JSON.stringify(point.latlng);

                    let marker = L.marker(point.latlng, {
                        title: title,
                        items: point.items
                    });

                    marker.bindPopup(title);
                    marker.on("click", evt => {
                        this.displayItems(evt.target.options.items);
                        this.applyVisibilityFilters();
                    });

                    marker.addTo(this.placeLayer);
                    this.allPlaceMarkers.push(marker);
                });

                Object.values(this.allItems).forEach(v => {
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

                this.displayAllItems();
            });
    }

    loadBallparkLayer() {
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
                            icon: this.stadiumIcon,
                            title: title
                        });
                    }
                });

                this.layerControl.addOverlay(ballparksLayer, "Present Day Ballparks");
            });
    }

    loadTeamLayer() {
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
                            icon: this.baseballCapIcon,
                            title: title
                        });
                    }
                });

                this.layerControl.addOverlay(ballparksLayer, "Teams");
            });
    }

    displayItems(itemIDs) {
        removeChildren(this.itemListing);

        itemIDs.forEach(itemID => {
            let item = this.allItems[itemID];
            // Convenience aliases
            let title = item.title;
            let meta = item.metadata;

            let itemContainer = document.createElement("li");
            itemContainer.classList.add("list-group-item", "item-listing");
            itemContainer.id = "item-" + itemID;
            itemContainer.dataset.itemID = itemID;
            this.itemListing.appendChild(itemContainer);

            let itemLink = document.createElement("a");
            itemLink.textContent = title;
            itemLink.href = meta["Digital ID URL"];
            itemLink.target = "_blank";

            itemLink.addEventListener("click", evt => {
                this.updateItemPreview(item);
                jQuery("#viewer-item-preview").modal();
                evt.preventDefault();
                evt.stopPropagation();
                return false;
            });

            itemContainer.appendChild(itemLink);
        });
    }

    displayAllItems() {
        this.displayItems(Object.values(this.allItems).map(v => v.id));
    }

    updateItemPreview(item) {
        let preview = $("#viewer-item-preview");
        $$(".title", preview).forEach(elem => (elem.textContent = item.title));
        $(".description", preview).textContent = item.metadata.Description;

        // Set the image to a 1px GIF to clear its contents so it won't display an
        // old image if the current one takes a long time to load:
        $("img", preview).src =
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";

        if (item.imageLarge) {
            $("img", preview).src = item.imageLarge;
            $(".item-image-container", preview).classList.remove("hidden");
        } else {
            $(".item-image-container", preview).classList.add("hidden");
        }

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
            if (field == "Digital ID URL") {
                let a = document.createElement("a");
                a.href = value;
                a.textContent = value;
                a.target = "_blank";
                td.appendChild(a);
            } else {
                td.textContent = value;
            }

            row.appendChild(td);

            tbody.appendChild(row);
        }
    }

    getVisibleItems() {
        // Apply search text filters:
        let searchText = this.textSearchInput.value.trim().toLocaleLowerCase();

        let visibleItems = Object.values(this.allItems)
            .filter(item => item.searchText.indexOf(searchText) > -1)
            .filter(
                item => item.startYear >= this.startYear && item.endYear <= this.endYear
            )
            .map(item => item.id);

        return visibleItems;
    }

    applyVisibilityFilters() {
        if (!this.allItems) {
            return;
        }

        let visibleItemIDs = this.getVisibleItems();

        $$(".item-listing", this.itemListing).forEach(node => {
            node.classList.toggle(
                "hidden",
                visibleItemIDs.indexOf(node.dataset.itemID) < 0
            );
        });

        let visibleItemCount = $$(".item-listing:not(.hidden)", this.itemListing)
            .length;

        $$(".item-count").forEach(elem => (elem.textContent = visibleItemCount));

        this.applyMapVisibilityFilter(visibleItemIDs);
    }

    applyMapVisibilityFilter(visibleItemIDs) {
        // Iterate over the points to see which one has at least one visible item

        let visibleIDSet = new Set(visibleItemIDs);

        this.allPlaceMarkers.forEach(marker => {
            let isVisible =
                marker.options.items.filter(i => visibleIDSet.has(i)).length > 0;

            if (isVisible) {
                this.placeLayer.addLayer(marker);
            } else {
                this.placeLayer.removeLayer(marker);
            }
        });
    }

    fitPlaces() {
        this.map.fitBounds(this.placeLayer.getBounds(), { animate: true });
    }

    setupTextSearch() {
        this.textSearchInput = $("#item-text-search");
        this.textSearchInput.addEventListener("input", () => {
            this.applyVisibilityFilters();
        });
    }

    setupTimeline() {
        let element = $("#slider");
        this.slider = element;

        noUiSlider.create(element, {
            start: [this.startYear, this.endYear],
            range: {
                min: this.startYear,
                max: this.endYear
            },
            format: {
                to: value => {
                    return value.toFixed(0);
                },
                from: value => {
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

            this.startYear = Math.floor(parseInt(values[0], 10) - 1);
            this.endYear = Math.ceil(parseInt(values[1], 10) + 1);

            this.applyVisibilityFilters();
        });
    }
}

window.viewer = new ItemViewer();
