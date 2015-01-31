var map;
var infowindow = new google.maps.InfoWindow();
currentFeature_or_Features = null;
var geojson;

function init(){
	map = new google.maps.Map(document.getElementById('map'),{
		zoom: 11,
		center: new google.maps.LatLng(1.3567, 103.82),
		mapTypeId: google.maps.MapTypeId.ROADMAP
	});

	geojson = {
		"type": "FeatureCollection",
		"features": []
	};
}
function ClearMap(){
	if (!currentFeature_or_Features)
		return;
	if (currentFeature_or_Features.length){
		for (var i = 0; i < currentFeature_or_Features.length; i++){
			if(currentFeature_or_Features[i].length){
				for(var j = 0; j < currentFeature_or_Features[i].length; j++){
					currentFeature_or_Features[i][j].setMap(null);
				}
			}
			else{
				currentFeature_or_Features[i].setMap(null);
			}
		}
	}else{
		currentFeature_or_Features.setMap(null);
	}
	if (infowindow.getMap()){
		infowindow.close();
	}
}
function SetCenter(lat, lng) {
	var myLatLng = new google.maps.LatLng(lat, lng);
	map.SetCenter(myLatLng)
}