mapboxgl.accessToken = 'pk.eyJ1IjoiZGF0YW1hbWExMTYiLCJhIjoiY2xncXMxM21rMTFhZDNybGh6cmE4YjZreCJ9.XPLngEtaW3V0Xd2vBDaxMQ'
const urlParams = new URLSearchParams(window.location.search);
const pntid = urlParams.get('srn');

function findFeatureBySRN(srnToFind) {
	for (var i = 0; i < infoData.features.length; i++) {
		if (infoData.features[i].properties.srn === srnToFind) {
			return infoData.features[i];
		}
	}
	return null; // Return null if the feature with the specified srn is not found
}
// Use the parameters to populate the article and zoom to the point
if (pntid) {
	var foundFeature = findFeatureBySRN(pntid);
	var startll = foundFeature.geometry.coordinates;
	console.log(startll)
}
else {
	var startll = [-83.6136, 43.7833];
}

// console.log(startll, startzoom)
var map = new mapboxgl.Map({
	container: 'map', // HTML container ID
	style:'mapbox://styles/datamama116/cll62uwv8008r01r8drpohcph',	
	center: startll, // starting position as [lng, lat]
	bbox:[-90.418136, 41.696118, -82.413474, 48.2388],
	zoom: 12,
	maxZoom: 16,
});
console.log(map)
// disable map rotation using right click + drag
map.dragRotate.disable();

// disable map rotation using touch rotation gesture
map.touchZoomRotate.disableRotation();


// Define bounds that conform to the `LngLatBoundsLike` object.
const bounds = [
[-91, 40], // [west, south]
[-80, 49]  // [east, north]
];
// Set the map's max bounds.

map.setMaxBounds(bounds);

// Add the control to the map.
map.addControl(
new MapboxGeocoder({
	
accessToken: mapboxgl.accessToken,
mapboxgl: mapboxgl,
zoom: 12,
countries: 'us',
bbox: [-90.418136, 41.696118, -82.413474, 48.2388],
limit:10,
types: 'poi,place,address',

})
);


// Functions
var popup = new mapboxgl.Popup({ closeButton: false, closeOnClick: true });

let hoverCurrentId = null
var datalayer;
document.addEventListener('click',function(e){
	if (e.target.id === 'source-button') {
		var button = e.target;
		var copiedURL = button.getAttribute('source-link');
		navigator.clipboard.writeText(copiedURL);

		button.textContent = 'Copied!';
		setTimeout(function () {
			button.innerHTML = '<i class="fa fa-link"></i> Copy Facility Link'
			// button.textContent = 'Share Link';
		}, 3500); // Reset the button text after 1.5 seconds
			}
})
function updateArticle(e) {
	let feature = e.features[0]
	var group_id = feature.properties.group_id
	var group_name = feature.properties.group_name
	var srn = feature.properties.srn
	var violation_count = feature.properties.violationCount
	var address = feature.properties.address_full
	var facility_name = feature.properties.facility_name
	var violation_article = feature.properties.violation_article
	// URL to copy
	var sourceURL = `https://planet-detroit.github.io/air-permit-violation-dashboard/?srn=${srn}`
	var shareBtn = `<button id="source-button" source-link="${sourceURL}"> <i class="fa fa-link"></i> Copy Facility Link</button>`
	if (group_id == 4) {
		var articleOpen = `<div class="epa-class-${group_id}"><h3 class="epa-class-dark">${group_name}</h3><h3 class="srn-dark">SRN: ${srn}</h3></div><div id="company-profile"><h3>${address}</h3><h1>${facility_name}</h1>`
	}
	else {
		var articleOpen = `<div class="epa-class-${group_id}"><h3 class="epa-class">${group_name}</h3><h3 class="srn">SRN: ${srn}</h3></div><div id="company-profile"><h3>${address}</h3><h1>${facility_name}</h1>`
	}

	if (violation_count > 1) {
		var vnCount = `<h2>${violation_count} Violation Notices</h2>`
	}
	else {
		
		var vnCount = `<h2>${violation_count} Violation Notice</h2>`
	}
	var articleClose = `</div><div id="share">${shareBtn}</div><div id="company-violations">${violation_article}</div>`

	var learn = `<div id='learn'><h4>Want to Learn More About This Facility?</h4><p>Find inspection reports, older violations and other documents for ${facility_name} in <a href="https://www.egle.state.mi.us/aps/downloads/SRN/${srn}" target="_blank">EGLE's database</a>, and use the <a href="https://www.michigan.gov/egle/-/media/Project/Websites/egle/Documents/Programs/AQD/misc-info/file-naming-convention.pdf" target="_blank">file naming conventions</a> to decode the documents (ie "SAR" = "Staff Activity Report", "ENFN" = "Enforcement Notice")</p><p>Explore all documents for permitted sources by browsing this <a href="https://www.tinyurl.com/egle-air-documents" target="_blank">Google sheet.</a> If you're looking for this facility, filter by its State Registration Number (SRN): ${srn}</p></div>`
	document.getElementById("articlePlace").innerHTML = articleOpen + vnCount + articleClose + learn
	articlePlace.scrollTop = 0
}

function startHover(e) {
	let feature = e.features[0]

	if (hoverCurrentId) {
		map.setFeatureState({ source: 'datalayer', id: hoverCurrentId }, { hover: false });
	}
	hoverCurrentId = feature.id
	map.setFeatureState({ source: 'datalayer', id: hoverCurrentId }, { hover: true });
}

function stopHover(e) {
	if (hoverCurrentId) {
		map.setFeatureState({ source: 'datalayer', id: hoverCurrentId }, { hover: false });
	}
	hoverCurrentId = null;
}

// Draw Popup
function drawPopup(e) {
	let feature = e.features[0]
	map.getCanvas().style.cursor = 'pointer';
	var coordinates = e.lngLat;//turf.centerOfMass(feature);
	var headline = feature.properties.facility_name;
	var violationCount = feature.properties.violationCount
	var group_id = feature.properties.group_id
	var group_name = feature.properties.group_name
	var group_name_simple = group_name.replace("Source","")
	console.log(feature.properties.most_recent_vn)
	var recent_vn = new Date(feature.properties.most_recent_vn.replace(/-/g, '\/'))
	var today = new Date()
	var duration = Math.round((today - recent_vn) / (1000 * 3600 * 24))
	function differenceInMonths(today, recent_vn) {
		const monthDiff = today.getMonth() - recent_vn.getMonth();
		const yearDiff = today.getYear() - recent_vn.getYear();

		return monthDiff + yearDiff * 12;
	}
	
	if (duration > 365) {
		duration = (today.getYear() - recent_vn.getYear()).toLocaleString()
		duration = duration + "+ YEARS AGO"
	}
	else if (duration > 31 ) {
		duration = differenceInMonths(today, recent_vn).toLocaleString()
		duration = duration + " MONTHS AGO"
	}
	else {
		duration = duration.toLocaleString() + " DAYS AGO"
	}
	
	var recent_vn_str = recent_vn.toLocaleDateString('en-us', {year:"numeric", month:"short"}).toUpperCase()
	while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
		coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
	}

	popup.setLngLat(coordinates)
		.setHTML(`<span class="pop-headline-${group_id}">${group_name_simple}</span><div class="pop-body"><span class="pop-facility-name">${headline}</span><br/><div class="pop-violation-count">${violationCount}</div><hr/><span style="font-size:1.3em;"><strong>Last Violation Notice</strong><br/>${duration}</span></div>`)
		.addTo(map);
}

function removePopup(e) {
	map.getCanvas().style.cursor = '';
	popup.remove();
}

function findFeatureBySRN(srnToFind) {
	for (var i = 0; i < infoData.features.length; i++) {
		if (infoData.features[i].properties.srn === srnToFind) {
			return infoData.features[i];
		}
	}
	return null; // Return null if the feature with the specified srn is not found
}
function updateArticle2(foundFeature) {
	let feature = foundFeature
	var group_id = feature.properties.group_id
	var group_name = feature.properties.group_name
	var srn = feature.properties.srn
	var violation_count = feature.properties.violationCount
	var address = feature.properties.address_full
	var facility_name = feature.properties.facility_name
	var violation_article = feature.properties.violation_article
	var sourceURL = `https://planet-detroit.github.io/air-permit-violation-dashboard/?srn=${srn}`
	var shareBtn = `<button id="source-button" source-link="${sourceURL}"> <i class="fa fa-link"></i> Copy Facility Link</button>`
	if (group_id == 4) {
		var articleOpen = `<div class="epa-class-${group_id}"><h3 class="epa-class-dark">${group_name}</h3><h3 class="srn-dark">SRN: ${srn}</h3></div><div id="company-profile"><h3>${address}</h3><h1>${facility_name}</h1>`
	}
	else {
		
		var articleOpen = `<div class="epa-class-${group_id}"><h3 class="epa-class">${group_name}</h3><h3 class="srn">SRN: ${srn}</h3></div><div id="company-profile"><h3>${address}</h3><h1>${facility_name}</h1>`
	}

	if (violation_count > 1) {
		var vnCount = `<h2>${violation_count} Violation Notices</h2>`
	}
	else {
		
		var vnCount = `<h2>${violation_count} Violation Notice</h2>`
	}
	var articleClose = `</div><div id="share">${shareBtn}</div><div id="company-violations">${violation_article}</div>`

	var learn = `<div id='learn'><h4>Want to Learn More About This Facility?</h4><p>Find inspection reports, older violations and other documents for ${facility_name} in <a href="https://www.egle.state.mi.us/aps/downloads/SRN/${srn}" target="_blank">EGLE's database</a>, and use the <a href="https://www.michigan.gov/egle/-/media/Project/Websites/egle/Documents/Programs/AQD/misc-info/file-naming-convention.pdf" target="_blank">file naming conventions</a> to decode the documents (ie "SAR" = "Staff Activity Report", "ENFN" = "Enforcement Notice")</p><p>Explore all documents for permitted sources by browsing this <a href="https://www.tinyurl.com/egle-air-documents" target="_blank">Google sheet.</a> If you're looking for this facility, filter by its State Registration Number (SRN): ${srn}</p></div>`
	document.getElementById("articlePlace").innerHTML = articleOpen + vnCount + articleClose + learn
	articlePlace.scrollTop = 0
}
var mapContainer = document.getElementById('map');

let newMarker; // Define the newMarker variable at the top level

function createNewMarker(ll) {
// Remove the existing marker if it exists
	if (newMarker) {
		removeNewMarker();
	}

// Create a new marker and setLngLat
	newMarker = new mapboxgl.Marker()
		.setLngLat(ll)
		.addTo(map);
	}

function removeNewMarker() {
if (newMarker) {
	newMarker.remove();
	newMarker = undefined; // Reset the newMarker variable
}
}
map.on('load', function () {
	for (let i = 0; i < infoData.features.length; i++) {
		infoData.features[i]['id'] = i + 1
	}
// Draw Facilities
	// map.setZoom(startzoom)
	// console.log(currentZoom)
	datalayer = map.addLayer({
		id: "datalayer",
		type: "circle",
		source: {
			type: "geojson",
			data: infoData,
		},
		paint: {
			'circle-radius': [
				'interpolate', ['exponential',2], ['zoom'], 
				5, ['interpolate', ['linear'],['get', 'violationCount'],
				1, 3,  // When the value is 0, the radius will be 5 pixels
				15, 18,
				35, 25  
				],
				12, ['interpolate', ['linear'], ['get','violationCount'],
				1, 9,
				15, 54,
				35, 75
			],
		],
			'circle-color': ['get', 'color'],
			'circle-opacity':[
				'case',
				['boolean', ['feature-state', 'hover'], false],
					1,
					0.5
				],

			'circle-opacity-transition': { duration: 300 }, // Smooth transition for opacity changes
			'circle-stroke-color': '#2E333F',  // Outline color
			'circle-stroke-width': .7, // Outline thickness
			'circle-stroke-opacity': .8
		}
	});
	

	// let currentCircle = null; // To keep track of the currently drawn circle
	
	// function drawCircle(coordinates) {
	// // Remove the previously drawn circle, if any
	// if (currentCircle) {
	// 	currentCircle.remove();
	// }

	// // Add a new circle
	// currentCircle = new mapboxgl.Marker({ color: 'blue' })
	// 	.setLngLat(coordinates)
	// 	.addTo(map);
	// }
// these functions control Mouse actions
// they make the pop-up headline or update the article text
// When we move the mouse over, draw the popup and change the hover style
	map.on('mousemove', 'datalayer', function (e) {
		startHover(e)
		drawPopup(e)
	});

	// When we move the mouse away from a point, turn off the hovering and popup
	map.on('mouseleave', 'datalayer', function (e) {
		stopHover(e)
		removePopup(e)
	});

	map.fitBounds(turf.bbox(infoData), { padding: 0, linear: true });

	if (pntid) {
	map.setZoom(12);
	mapContainer.scrollIntoView({behavior: "smooth", block: "start", inline: "start"});
	var foundFeature = findFeatureBySRN(pntid);
	var ll = startll;
	createNewMarker(ll);
	updateArticle2(foundFeature);
	}
	
	// When we click, update the article (the right-hand side)
	map.on('click', 'datalayer', function (e) {
		
		if (newMarker) {
			removeNewMarker(newMarker)
		}

		
		var ll = e.features[0].geometry.coordinates

		createNewMarker(ll)
		updateArticle(e)
		var currentZoom = map.getZoom();
		
		if (currentZoom < 12) {
		map.flyTo({
		center: e.features[0].geometry.coordinates,
		zoom:12,
		});
	}
		else if (currentZoom == 12) {
		map.flyTo({
		center: e.features[0].geometry.coordinates,
		duration: 1000,
		essential: true
		});
	}
		else if (currentZoom > 12) {
		map.flyTo({
		center: e.features[0].geometry.coordinates,
		essential: true,
		duration: 1000
		// zoom:12,
		});
	
	}
		
	// const coordinates = e.features[0].geometry.coordinates;

	// // Call the drawCircle function with the coordinates
	// drawCircle(coordinates);
	});
})




// this part is J query / with some mapbox JavaScript
// it changes what is displayed based on the pulldown menu

var groupsObj = {};

$(document).ready(function () {
	infoData.features.forEach(function (feature) {
		groupsObj[feature.properties.group_id] = feature.properties.group_name;
	})

	$.each(groupsObj, function (key, value) {
		$('#select-menu')
			.append($("<option></option>")
				.attr("value", value)
				.text(value));
	});

	$('#select-menu').change(function () {
		var selectedGroup = $('#select-menu').val();

		if (!selectedGroup) {
			map.setFilter('datalayer', null);
		} else {
			map.setFilter('datalayer', ['==', ['get', 'group_name'], selectedGroup]);
		}
	});
});

// Get the Epa Modal
var epaModal = document.getElementById("epaPopup");
// var epaModal2 = document.getElementById("epaPopup2");

// Get the Epa Button that opens the modal
var epaBtn = document.getElementById("epaButton");

// Get the Epa Button that opens the modal
var epaBtn2 = document.getElementById("epaButton2");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];
// var span2 = document.getElementsByClassName("close2")[0];

// When the user clicks the button, open the modal 
epaBtn.onclick = function() {
epaModal.style.display = "block";
}
// When the user clicks the button, open the modal 
epaBtn2.onclick = function() {
epaModal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
epaModal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
if (event.target == epaModal) {
epaModal.style.display = "none";
}
}



let newViolations = violationData.features
let violationDivs = ``

newViolations.forEach((item) => {
let epa_class = item.properties.group_name
let group_id = item.properties.group_id
let facility_name = item.properties.facility_name
let date_str = item.properties.date_str
let violation_comment_list = item.properties.comment_list
let doc_url = item.properties.doc_url
var geom = item.geometry.coordinates
var lat = item.properties.lat
var long = item.properties.long
var id = item.properties.srn
var county = item.properties.county
// let violation_comments = "<ul><li>" + violation_comment_list.join("</li><li>") + "</li></ul>"

// Getting ready to count characters
let totalCharacters = 0;

// Calculating the total characters
for (let i = 0; i < violation_comment_list.length; i++) {
totalCharacters += violation_comment_list[i].length;
}

let violation_comments = ""

// If there are more than 1 violation comment, make a list
if (violation_comment_list.length > 1) {
	violation_comments = "<ul><li>" + violation_comment_list.join("</li><li>") + "</li></ul>"
}
// Otherwise save the first item in the list
else {
	violation_comments = violation_comment_list[0]
}

const maxLength = 500;

// Now let's limit the character length if it's over 500 characters
function limitCharacterLength(inputString, maxLength) {
if (inputString.length > maxLength) {
    // 
	return `<div id="map-link"><p>` + inputString.slice(0, maxLength)+`...<a class="read-more" data-lat="${lat}" data-long="${long}" data-id="${id}">[Read more]</a></p>`; // Truncate the string to the desired length
}
return `<p>`+ inputString + `</p><div id="map-link">`; // If the string is already within the limit, return it as is
}

// // Limit the character length to 200 characters

violation_comments = limitCharacterLength(violation_comments, maxLength);

if (group_id == 4){
	var oneDivOpen = `<div class="one-vn"><div class="epa-class-${group_id}"><h3 class="dark">${epa_class}</h3></div>`
}
else {
	var oneDivOpen = `<div class="one-vn"><div class="epa-class-${group_id}"><h3>${epa_class}</h3></div>`
}

var oneDivClose = `<div class="snippet"><h5>${county} County</h5><h1>${facility_name}</h1><a href="${doc_url}" target="_blank">${date_str}</a><img class="icon" src="img/doc-link.svg"/>${violation_comments}<a class="article" data-lat="${lat}" data-long="${long}" data-id="${id}">View on the map &#8594;</a></div></div></div>`

var oneDiv = oneDivOpen + oneDivClose

violationDivs = violationDivs + oneDiv

})

document.getElementById("recent-violations").innerHTML = violationDivs

$(document).on('click', '#map-link a', function(e) {
// lngLat = $(this).attr('data-coord')
// lngLat = $(this).attr(data-geom)
var id = $(this).attr('data-id')
var ll = new mapboxgl.LngLat($(this).attr('data-long'), $(this).attr('data-lat'));
createNewMarker(ll)
// new LngLat(lng: number, lat: number)
map.flyTo({
		center:ll,
		duration:100,
		zoom:12,
})


var mapContainer = document.getElementById('map');
const timer = setTimeout(() => {

	if (!mapContainer) {
	  return;
	}

	mapContainer.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"});
  }, 200);

var srnToSearchFor = id; // Replace with the SRN you want to find
var foundFeature = findFeatureBySRN(srnToSearchFor);
updateArticle2(foundFeature)

})
document.addEventListener("DOMContentLoaded", function () {
    const loadMoreButton = document.getElementById("loadMoreButton");
    const hiddenDivs = document.querySelectorAll(".one-vn:nth-child(n+7)");
  
    loadMoreButton.addEventListener("click", function () {
      hiddenDivs.forEach(function (div) {
        div.style.display = "block";
      });
      loadMoreButton.style.display = "none"; // Optionally hide the button after loading all divs
    });
  });
  $(document).on('click', '#data-table a', function(e) {
	var id = $(this).attr('data-id')
	// var mapContainer = document.getElementById('map');
	// mapContainer.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"});
	var srnToSearchFor = id; // Replace with the SRN you want to find
	var foundFeature = findFeatureBySRN(srnToSearchFor);
	var ll = foundFeature.geometry.coordinates;
	map.flyTo({
			center:ll,
			duration:100,
			zoom:12,
	})

	updateArticle2(foundFeature)
	createNewMarker(ll)
	})