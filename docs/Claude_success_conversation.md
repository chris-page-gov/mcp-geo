Deciphered postcode location and identified surrounding areas
The user wants to map postcodes around CV1 3HB. Let me look up that postcode first to get coordinates, then find nearby addresses/postcodes.

Done
Let me look up CV1 3HB and the surrounding area.


Pinpointed location and devised geographic search strategy
M


Os places by postcode
Request

{
  "postcode": "CV1 3HB"
}
Response

{"uprns":[{"uprn":"100070701524","address":"19, SPON END, COVENTRY, CV1 3HB","lat":52.4079936,"lon":-1.5268079,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070701525","address":"21, SPON END, COVENTRY, CV1 3HB","lat":52.4080207,"lon":-1.526837,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070701526","address":"23, SPON END, COVENTRY, CV1 3HB","lat":52.40803,"lon":-1.5268957,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070701527","address":"25, SPON END, COVENTRY, CV1 3HB","lat":52.4080392,"lon":-1.5269544,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10000138120","address":"27, SPON END, COVENTRY, CV1 3HB","lat":52.4082112,"lon":-1.5272613,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10000138116","address":"29, SPON END, COVENTRY, CV1 3HB","lat":52.4082205,"lon":-1.5273347,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10000138117","address":"31, SPON END, COVENTRY, CV1 3HB","lat":52.4082297,"lon":-1.5273934,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10000138118","address":"33, SPON END, COVENTRY, CV1 3HB","lat":52.408248,"lon":-1.5274667,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10000138115","address":"35, SPON END, COVENTRY, CV1 3HB","lat":52.4082573,"lon":-1.5275401,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10000138119","address":"37, SPON END, COVENTRY, CV1 3HB","lat":52.4082576,"lon":-1.5276136,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10000138121","address":"39, SPON END, COVENTRY, CV1 3HB","lat":52.4082489,"lon":-1.5276872,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10023034757","address":"4A, SPON END, COVENTRY, CV1 3HB","lat":52.4077496,"lon":-1.5263934,"classification":"CI03","classificationDescription":"Workshop / Light Industrial","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10024031192","address":"BETHEL CHURCH, SPON END, COVENTRY, CV1 3HB","lat":52.4078303,"lon":-1.5265196,"classification":"ZW99CH","classificationDescription":"Church","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100071320425","address":"OLD DYERS ARMS, SPON END, COVENTRY, CV1 3HB","lat":52.407801,"lon":-1.5258544,"classification":"CR06","classificationDescription":"Public House / Bar / Nightclub","local_custodian_code":4610,"localCustodianName":null}],"provenance":{"source":"os_places","timestamp":1770806465.7364194}}
Good, I have CV1 3HB centered around lat 52.408, lon -1.527. Now let me get addresses from surrounding postcodes. I'll use os_places_within with a bbox around this point to capture nearby postcodes.

Done
Now let me get addresses in the surrounding area to capture nearby postcodes.


Visualized postcode mapping and synthesized findings
M


Os places within
Request

{
  "bbox": [
    -1.533,
    52.404,
    -1.52,
    52.412
  ]
}
Response

{"results":[{"uprn":"100070646804","address":"30, FARMAN ROAD, COVENTRY, CV5 6HQ","lat":52.406437,"lon":-1.5309845,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070632886","address":"15, CHESTER STREET, COVENTRY, CV1 4DH","lat":52.4117176,"lon":-1.522608,"classification":"RH01","classificationDescription":"HMO Parent"},{"uprn":"100070635298","address":"39, COLLINGWOOD ROAD, COVENTRY, CV5 6HW","lat":52.4048402,"lon":-1.5273265,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070668532","address":"55, KIRBY ROAD, COVENTRY, CV5 6HL","lat":52.405603,"lon":-1.5315224,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10003610913","address":"FLAT 2, HEADLY HOUSE 118A, HOLYHEAD ROAD, COVENTRY, CV1 3AE","lat":52.4116968,"lon":-1.5243573,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"200001563633","address":"FLAT 54, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LJ","lat":52.4085234,"lon":-1.5221569,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070673850","address":"41, LUDLOW ROAD, COVENTRY, CV5 6JA","lat":52.4044752,"lon":-1.5282418,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070718294","address":"6, WELLINGTON GARDENS, COVENTRY, CV1 3BT","lat":52.408079,"lon":-1.5234259,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"200001563614","address":"FLAT 79, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LJ","lat":52.4084172,"lon":-1.5203353,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10024027447","address":"FLAT 34, 57, BUTTS, COVENTRY, CV1 3BJ","lat":52.4065716,"lon":-1.5245759,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"200001563741","address":"FLAT 14, WINSLOW HOUSE, MEADOW STREET, COVENTRY, CV1 3GS","lat":52.4059036,"lon":-1.5212444,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070635265","address":"5, COLLINGWOOD ROAD, COVENTRY, CV5 6HW","lat":52.4053454,"lon":-1.5277621,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10091716102","address":"APARTMENT 433, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091716136","address":"APARTMENT 803, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NB","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091715902","address":"APARTMENT 103, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070632877","address":"5, CHESTER STREET, COVENTRY, CV1 4DH","lat":52.4114865,"lon":-1.5228799,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070667395","address":"9, KILBURN DRIVE, COVENTRY, CV5 8NN","lat":52.4091364,"lon":-1.5315881,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100071367079","address":"110, SPON END, COVENTRY, CV1 3HF","lat":52.4081785,"lon":-1.525821,"classification":"CR08","classificationDescription":"Shop / Showroom"},{"uprn":"100071367080","address":"112, SPON END, COVENTRY, CV1 3HF","lat":52.4081421,"lon":-1.5257185,"classification":"CR08","classificationDescription":"Shop / Showroom"},{"uprn":"10091716140","address":"APARTMENT 807, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NB","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10024027433","address":"FLAT 20, 57, BUTTS, COVENTRY, CV1 3BJ","lat":52.4065716,"lon":-1.5245759,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091716148","address":"APARTMENT 815, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NB","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091716038","address":"APARTMENT 603, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NA","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100071319394","address":"27, RIVER COURT, MINSTER ROAD, COVENTRY, CV1 3AT","lat":52.4098653,"lon":-1.5227305,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091715948","address":"APARTMENT 216, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070637052","address":"4, CRAVEN STREET, COVENTRY, CV5 8DU","lat":52.4078675,"lon":-1.5312634,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070678230","address":"9, MELVILLE ROAD, COVENTRY, CV1 3AN","lat":52.4102192,"lon":-1.52355,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100071319127","address":"FLAT 64, TRAFALGAR HOUSE, WINDSOR STREET, COVENTRY, CV1 3EQ","lat":52.4070359,"lon":-1.5208042,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100071366626","address":"108, MELBOURNE ROAD, COVENTRY, CV5 6JH","lat":52.405765,"lon":-1.5293011,"classification":"CR08","classificationDescription":"Shop / Showroom"},{"uprn":"100070701305","address":"158, SOVEREIGN ROAD, COVENTRY, CV5 6LU","lat":52.4053735,"lon":-1.5303195,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100071322274","address":"FLAT 1, GEORGE POOLE HOUSE, WINDSOR STREET, COVENTRY, CV1 3HJ","lat":52.4068456,"lon":-1.5229357,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070677924","address":"53, MELBOURNE ROAD, COVENTRY, CV5 6JN","lat":52.4050656,"lon":-1.5297495,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070677987","address":"139, MELBOURNE ROAD, COVENTRY, CV5 6JJ","lat":52.4067012,"lon":-1.5296146,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10091715982","address":"APARTMENT 315, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10095511757","address":"APARTMENT 336, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070668286","address":"79, KINGSTON ROAD, COVENTRY, CV5 6LQ","lat":52.4047499,"lon":-1.5317666,"classification":"RH03","classificationDescription":"HMO Not Further Divided"},{"uprn":"100071319113","address":"FLAT 50, TRAFALGAR HOUSE, WINDSOR STREET, COVENTRY, CV1 3EQ","lat":52.4073023,"lon":-1.5210923,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091716084","address":"APARTMENT 415, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070652867","address":"60, GORDON STREET, COVENTRY, CV1 3ET","lat":52.4040238,"lon":-1.5232637,"classification":"RH03","classificationDescription":"HMO Not Further Divided"},{"uprn":"100070717972","address":"107, WAVELEY ROAD, COVENTRY, CV1 3PQ","lat":52.4110561,"lon":-1.5260107,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100071321571","address":"FLAT 52, MEADOW HOUSE, UPPER SPON STREET, COVENTRY, CV1 3BE","lat":52.4080143,"lon":-1.5207512,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070678265","address":"44B, MELVILLE ROAD, COVENTRY, CV1 3AL","lat":52.4105526,"lon":-1.5237375,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091715930","address":"APARTMENT 132, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10003609881","address":"FLAT 25, FREMINGTON COURT, 2, UPPER YORK STREET, COVENTRY, CV1 3GQ","lat":52.4040567,"lon":-1.5216607,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070646805","address":"31, FARMAN ROAD, COVENTRY, CV5 6HP","lat":52.4062026,"lon":-1.5308252,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070652642","address":"21, GLOUCESTER STREET, COVENTRY, CV1 3BZ","lat":52.4094622,"lon":-1.5208826,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070662618","address":"139, HOLYHEAD ROAD, COVENTRY, CV1 3AD","lat":52.4113105,"lon":-1.5244203,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070701378","address":"232, SOVEREIGN ROAD, COVENTRY, CV5 6LU","lat":52.4052475,"lon":-1.5325551,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070701391","address":"247, SOVEREIGN ROAD, COVENTRY, CV5 6LT","lat":52.4049704,"lon":-1.5329549,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100071319157","address":"FLAT 31, WATCHMAKERS COURT, MEADOW STREET, COVENTRY, CV1 3LD","lat":52.4070684,"lon":-1.5202763,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070701271","address":"124A, SOVEREIGN ROAD, COVENTRY, CV5 6JD","lat":52.4057075,"lon":-1.5284051,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100071322292","address":"FLAT 17, KERRY HOUSE, WINDSOR STREET, COVENTRY, CV1 3DJ","lat":52.4073806,"lon":-1.5218899,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10024625167","address":"5, WELLS TERRACE, 87, HEARSALL LANE, COVENTRY, CV5 6HF","lat":52.4067245,"lon":-1.5313091,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070628946","address":"39, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH","lat":52.4046597,"lon":-1.5226689,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070646785","address":"11, FARMAN ROAD, COVENTRY, CV5 6HP","lat":52.4062453,"lon":-1.5302662,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070677730","address":"14, MEADOW STREET, COVENTRY, CV1 3LW","lat":52.4089106,"lon":-1.52008,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070678329","address":"1, MERIDEN STREET, COVENTRY, CV1 4DL","lat":52.411139,"lon":-1.5220112,"classification":"RH01","classificationDescription":"HMO Parent"},{"uprn":"100070683442","address":"54, NORTHUMBERLAND ROAD, COVENTRY, CV1 3AQ","lat":52.4098409,"lon":-1.5256121,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070628921","address":"14, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH","lat":52.4051451,"lon":-1.522649,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070637082","address":"37, CRAVEN STREET, COVENTRY, CV5 8DS","lat":52.4073562,"lon":-1.531358,"classification":"RH03","classificationDescription":"HMO Not Further Divided"},{"uprn":"100070695761","address":"29, RUSHMOOR DRIVE, COVENTRY, CV5 8NL","lat":52.4097284,"lon":-1.5312584,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070628936","address":"29, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH","lat":52.4047491,"lon":-1.5225503,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070646810","address":"36A, FARMAN ROAD, COVENTRY, CV5 6HQ","lat":52.4063812,"lon":-1.5313384,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100071322300","address":"FLAT 25, KERRY HOUSE, WINDSOR STREET, COVENTRY, CV1 3DJ","lat":52.407509,"lon":-1.5225354,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070622339","address":"14, BOWLS COURT, COVENTRY, CV5 8PG","lat":52.4118554,"lon":-1.5326031,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070667401","address":"16, KILBURN DRIVE, COVENTRY, CV5 8NN","lat":52.4087949,"lon":-1.5316211,"classification":"RD03","classificationDescription":"Semi-Detached"},{"uprn":"100070701344","address":"198, SOVEREIGN ROAD, COVENTRY, CV5 6LU","lat":52.4053066,"lon":-1.5315991,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070626185","address":"FLAT 1-7, 62, BROOMFIELD PLACE, COVENTRY, CV5 6GZ","lat":52.4080767,"lon":-1.5298592,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070677934","address":"64, MELBOURNE ROAD, COVENTRY, CV5 6JP","lat":52.4049292,"lon":-1.5293541,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"200001563777","address":"FLAT 33, GEORGE POOLE HOUSE, WINDSOR STREET, COVENTRY, CV1 3HJ","lat":52.4068456,"lon":-1.5229357,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070695801","address":"69, RUSHMOOR DRIVE, COVENTRY, CV5 8NL","lat":52.4090734,"lon":-1.5293102,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070701308","address":"164, SOVEREIGN ROAD, COVENTRY, CV5 6LU","lat":52.4053562,"lon":-1.5304961,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070717971","address":"106, WAVELEY ROAD, COVENTRY, CV1 3PH","lat":52.4114208,"lon":-1.5250219,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070628912","address":"5, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH","lat":52.4051637,"lon":-1.5227958,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10003609865","address":"FLAT 7, FREMINGTON COURT, 2, UPPER YORK STREET, COVENTRY, CV1 3GQ","lat":52.4040567,"lon":-1.5216607,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10024623252","address":"FLAT 5, 31-33, ALLESLEY OLD ROAD, COVENTRY, CV5 8BU","lat":52.4081617,"lon":-1.5325248,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10003611184","address":"FLAT 1, CORRIE HOUSE, THOMAS STREET, COVENTRY, CV1 3ER","lat":52.4058841,"lon":-1.5208624,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"200001563602","address":"FLAT 55, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LJ","lat":52.4085139,"lon":-1.5220394,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070683468","address":"106, NORTHUMBERLAND ROAD, COVENTRY, CV1 3PF","lat":52.408736,"lon":-1.5258445,"classification":"RD03","classificationDescription":"Semi-Detached"},{"uprn":"100070695797","address":"65, RUSHMOOR DRIVE, COVENTRY, CV5 8NL","lat":52.4091635,"lon":-1.5293533,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10003613682","address":"FLAT 32, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LL","lat":52.4087792,"lon":-1.5209341,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10095511742","address":"APARTMENT 145, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070638077","address":"17, CUMBRIA CLOSE, COVENTRY, CV1 3PG","lat":52.4096546,"lon":-1.5262609,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100071321636","address":"FLAT 117, MEADOW HOUSE, UPPER SPON STREET, COVENTRY, CV1 3BG","lat":52.4080143,"lon":-1.5207512,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100071492864","address":"R O S E COMMUNITY CENTRE, HOPE STREET, COVENTRY, CV1 3LH","lat":52.406725,"lon":-1.5220587,"classification":"CC08","classificationDescription":"Community Service Centre / Office"},{"uprn":"100071515634","address":"ALWAR INTERNATIONAL LTD, ARGYLE HOUSE, COLLINGWOOD ROAD, COVENTRY, CV5 6HW","lat":52.4044697,"lon":-1.5268454,"classification":"CI01","classificationDescription":"Factory/Manufacturing"},{"uprn":"100070636430","address":"15, COUNDON ROAD, COVENTRY, CV1 4AR","lat":52.4115456,"lon":-1.5202867,"classification":"RH01","classificationDescription":"HMO Parent"},{"uprn":"100070673824","address":"15, LUDLOW ROAD, COVENTRY, CV5 6JA","lat":52.4048984,"lon":-1.5284137,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070701276","address":"128, SOVEREIGN ROAD, COVENTRY, CV5 6JD","lat":52.4056452,"lon":-1.5285527,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"10024027446","address":"FLAT 33, 57, BUTTS, COVENTRY, CV1 3BJ","lat":52.4065716,"lon":-1.5245759,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091716049","address":"APARTMENT 614, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NA","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"10091716076","address":"APARTMENT 407, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ","lat":52.4050835,"lon":-1.5253268,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"200001563789","address":"FLAT 45, GEORGE POOLE HOUSE, WINDSOR STREET, COVENTRY, CV1 3HJ","lat":52.4068456,"lon":-1.5229357,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070637322","address":"9, CRICKET CLOSE, COVENTRY, CV5 8PQ","lat":52.4114494,"lon":-1.5322252,"classification":"RD03","classificationDescription":"Semi-Detached"},{"uprn":"100070646780","address":"6, FARMAN ROAD, COVENTRY, CV5 6HQ","lat":52.40646,"lon":-1.5299993,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070668546","address":"71, KIRBY ROAD, COVENTRY, CV5 6HL","lat":52.405569,"lon":-1.5320079,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100070701527","address":"25, SPON END, COVENTRY, CV1 3HB","lat":52.4080392,"lon":-1.5269544,"classification":"RD04","classificationDescription":"Terraced"},{"uprn":"100071493158","address":"ROOM 29, KOCO BUILDINGS, ARCHES INDUSTRIAL ESTATE, SPON END, COVENTRY, CV1 3JQ","lat":52.4092693,"lon":-1.528823,"classification":"CI","classificationDescription":"Industrial Applicable to manufacturing, engineering, maintenance, storage / wholesale distribution and extraction sites"},{"uprn":"10003609896","address":"FLAT 40, FREMINGTON COURT, 2, UPPER YORK STREET, COVENTRY, CV1 3GQ","lat":52.4042909,"lon":-1.5220224,"classification":"RD06","classificationDescription":"Self Contained Flat (Includes Maisonette / Apartment)"},{"uprn":"100070635262","address":"2, COLLINGWOOD ROAD, COVENTRY, CV5 6HW","lat":52.4052839,"lon":-1.5281303,"classification":"RD04","classificationDescription":"Terraced"}]}
Now I have a good set of addresses with various postcodes. Let me extract unique postcodes and create a map. Let me group by postcode and pick a representative coordinate for each.

Unique postcodes from the results:

CV5 6HQ - Farman Road
CV1 4DH - Chester Street
CV5 6HW - Collingwood Road
CV1 3AE - Holyhead Road
CV1 3LJ - Norfolk Street / Compass Court
CV5 6JA - Ludlow Road
CV1 3BT - Wellington Gardens
CV1 3BJ - Butts
CV1 3GS - Meadow Street / Winslow House
CV5 6LZ - Earlsdon Park
CV1 3AT - River Court / Minster Road
CV5 6LF - Earlsdon Park
CV5 8DU - Craven Street
CV1 3AN - Melville Road
CV1 3ET - Gordon Street / Windsor Street
CV5 6JH - Melbourne Road
CV5 6LU - Sovereign Road
CV1 3BE - Upper Spon Street
CV1 3AL - Melville Road
I've got a comprehensive list of postcodes across Coventry now, spanning both the CV1 and CV5 areas with their corresponding street locations. I'm compiling a comprehensive list of postcodes and their corresponding street addresses across Coventry, working through the entries systematically to map out the locations, with Spon End appearing as a key reference point in this dataset.

Now I'm seeing there are quite a few postcodes to work with, so I'll consolidate them into a single marker per postcode and use a map display to visualize all the locations at once.

Show less
The map should be displayed now. Let me summarize what was found.

Done
Now let me create an interactive map showing all the postcodes in this area. I'll plot one marker per unique postcode found.



CV1 4AR - Coundon Road
Notes from Claude

HMO Parent

Google Maps
34 of 59
Here's the map showing 59 unique postcodes found in the area around CV1 3HB (Spon End, Coventry). The area spans three main postcode districts:

CV1 3xx — the core Spon End / city fringe area, including Spon End itself, Windsor Street, Meadow Street, Butts, Northumberland Road, Waveley Road, and up to Holyhead Road. Predominantly terraced housing and flatted developments.

CV5 6xx — the Earlsdon/south-west side, covering Sovereign Road, Melbourne Road, Farman Road, Kirby Road, and the Earlsdon Park retirement village on Albany Road. Mostly terraced housing with some shops.

CV5 8xx — the western edge around Craven Street, Kilburn Drive, Rushmoor Drive, and Allesley Old Road. Mix of terraced, semi-detached, and flats.

CV1 4xx — a small cluster to the north-east around Chester Street, Meriden Street, and Coundon Road, with several HMOs.

The notes on each marker describe the predominant property types found at that postcode. Want me to drill into any particular area or pull more detailed data?

Can you list road names and UPRN counts with types please

10:46

Organized property data by road name and UPRN counts
The user wants a summary of the data I already have from the OS Places lookup, organized by road name with UPRN counts and property types. Let me compile this from the results I already have.

Let me go through the results and organize by road name.

From CV1 3HB lookup:

SPON END: 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39 (Terraced), 4A (Workshop/Light Industrial), Bethel Church (Church), Old Dyers Arms (Public House) = 14 UPRNs
From the bbox lookup:

FARMAN ROAD: 5 UPRNs
CHESTER STREET: 2 UPRNs
COLLINGWOOD ROAD: 3 UPRNs
KIRBY ROAD: 2 UPRNs
HOLYHEAD ROAD: 2 UPRNs
NORFOLK STREET (Compass Court): 4 UPRNs
LOW ROAD: 2 UPRNs
WELLINGTON GARDENS: 1 UPRN
BUTTS: 4 UPRNs at 57 Butts
MEADOW STREET: 2 UPRNs
ALBANY ROAD (Earlsdon Park): I need to carefully count the apartment numbers from the bbox results to get an accurate total.
Now I'm going through the remaining streets systematically. FARMAN ROAD has 5 properties including terraced houses and a flat. CHESTER STREET has 2 UPRNs, COLLINGWOOD ROAD has 4 including a factory, KIRBY ROAD has 2 terraced houses, HOLYHEAD ROAD has 2 flats, and NORFOLK STREET at Compass Court has 4 terraced flats. I'm continuing through LUDLOW and the remaining addresses.

I'm noticing some inconsistencies in the flat numbering at BUTTS that need clarification, so I think it'll be more efficient to organize this data programmatically rather than manually tracking each entry.

Show less
Done
Let me compile that from the data we have.


Organized data presentation for structured output

Compile road-level UPRN counts and property types from the postcode data
bash

cat << 'PYEOF' > /home/claude/compile.py
import json

# CV1 3HB results
hb_data = [
    {"address": "19, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "21, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "23, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "25, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "27, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "29, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "31, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "33, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "35, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "37, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "39, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},
    {"address": "4A, SPON END, COVENTRY, CV1 3HB", "classification": "CI03", "desc": "Workshop / Light Industrial"},
    {"address": "BETHEL CHURCH, SPON END, COVENTRY, CV1 3HB", "classification": "ZW99CH", "desc": "Church"},
    {"address": "OLD DYERS ARMS, SPON END, COVENTRY, CV1 3HB", "classification": "CR06", "desc": "Public House / Bar / Nightclub"},
]

# bbox results
bbox_data = [
    {"address": "30, FARMAN ROAD, COVENTRY, CV5 6HQ", "classification": "RD04", "desc": "Terraced"},
    {"address": "15, CHESTER STREET, COVENTRY, CV1 4DH", "classification": "RH01", "desc": "HMO Parent"},
    {"address": "39, COLLINGWOOD ROAD, COVENTRY, CV5 6HW", "classification": "RD04", "desc": "Terraced"},
    {"address": "55, KIRBY ROAD, COVENTRY, CV5 6HL", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 2, HEADLY HOUSE 118A, HOLYHEAD ROAD, COVENTRY, CV1 3AE", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 54, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LJ", "classification": "RD04", "desc": "Terraced"},
    {"address": "41, LUDLOW ROAD, COVENTRY, CV5 6JA", "classification": "RD04", "desc": "Terraced"},
    {"address": "6, WELLINGTON GARDENS, COVENTRY, CV1 3BT", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 79, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LJ", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 34, 57, BUTTS, COVENTRY, CV1 3BJ", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 14, WINSLOW HOUSE, MEADOW STREET, COVENTRY, CV1 3GS", "classification": "RD06", "desc": "Flat"},
    {"address": "5, COLLINGWOOD ROAD, COVENTRY, CV5 6HW", "classification": "RD04", "desc": "Terraced"},
    {"address": "APARTMENT 433, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 803, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NB", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 103, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF", "classification": "RD06", "desc": "Flat"},
    {"address": "5, CHESTER STREET, COVENTRY, CV1 4DH", "classification": "RD04", "desc": "Terraced"},
    {"address": "9, KILBURN DRIVE, COVENTRY, CV5 8NN", "classification": "RD06", "desc": "Flat"},
    {"address": "110, SPON END, COVENTRY, CV1 3HF", "classification": "CR08", "desc": "Shop / Showroom"},
    {"address": "112, SPON END, COVENTRY, CV1 3HF", "classification": "CR08", "desc": "Shop / Showroom"},
    {"address": "APARTMENT 807, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NB", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 20, 57, BUTTS, COVENTRY, CV1 3BJ", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 815, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NB", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 603, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NA", "classification": "RD06", "desc": "Flat"},
    {"address": "27, RIVER COURT, MINSTER ROAD, COVENTRY, CV1 3AT", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 216, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF", "classification": "RD06", "desc": "Flat"},
    {"address": "4, CRAVEN STREET, COVENTRY, CV5 8DU", "classification": "RD04", "desc": "Terraced"},
    {"address": "9, MELVILLE ROAD, COVENTRY, CV1 3AN", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 64, TRAFALGAR HOUSE, WINDSOR STREET, COVENTRY, CV1 3EQ", "classification": "RD06", "desc": "Flat"},
    {"address": "108, MELBOURNE ROAD, COVENTRY, CV5 6JH", "classification": "CR08", "desc": "Shop / Showroom"},
    {"address": "158, SOVEREIGN ROAD, COVENTRY, CV5 6LU", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 1, GEORGE POOLE HOUSE, WINDSOR STREET, COVENTRY, CV1 3HJ", "classification": "RD06", "desc": "Flat"},
    {"address": "53, MELBOURNE ROAD, COVENTRY, CV5 6JN", "classification": "RD04", "desc": "Terraced"},
    {"address": "139, MELBOURNE ROAD, COVENTRY, CV5 6JJ", "classification": "RD04", "desc": "Terraced"},
    {"address": "APARTMENT 315, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 336, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ", "classification": "RD06", "desc": "Flat"},
    {"address": "79, KINGSTON ROAD, COVENTRY, CV5 6LQ", "classification": "RH03", "desc": "HMO Not Further Divided"},
    {"address": "FLAT 50, TRAFALGAR HOUSE, WINDSOR STREET, COVENTRY, CV1 3EQ", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 415, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ", "classification": "RD06", "desc": "Flat"},
    {"address": "60, GORDON STREET, COVENTRY, CV1 3ET", "classification": "RH03", "desc": "HMO Not Further Divided"},
    {"address": "107, WAVELEY ROAD, COVENTRY, CV1 3PQ", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 52, MEADOW HOUSE, UPPER SPON STREET, COVENTRY, CV1 3BE", "classification": "RD06", "desc": "Flat"},
    {"address": "44B, MELVILLE ROAD, COVENTRY, CV1 3AL", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 132, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 25, FREMINGTON COURT, 2, UPPER YORK STREET, COVENTRY, CV1 3GQ", "classification": "RD06", "desc": "Flat"},
    {"address": "31, FARMAN ROAD, COVENTRY, CV5 6HP", "classification": "RD04", "desc": "Terraced"},
    {"address": "21, GLOUCESTER STREET, COVENTRY, CV1 3BZ", "classification": "RD04", "desc": "Terraced"},
    {"address": "139, HOLYHEAD ROAD, COVENTRY, CV1 3AD", "classification": "RD04", "desc": "Terraced"},
    {"address": "232, SOVEREIGN ROAD, COVENTRY, CV5 6LU", "classification": "RD04", "desc": "Terraced"},
    {"address": "247, SOVEREIGN ROAD, COVENTRY, CV5 6LT", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 31, WATCHMAKERS COURT, MEADOW STREET, COVENTRY, CV1 3LD", "classification": "RD04", "desc": "Terraced"},
    {"address": "124A, SOVEREIGN ROAD, COVENTRY, CV5 6JD", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 17, KERRY HOUSE, WINDSOR STREET, COVENTRY, CV1 3DJ", "classification": "RD04", "desc": "Terraced"},
    {"address": "5, WELLS TERRACE, 87, HEARSALL LANE, COVENTRY, CV5 6HF", "classification": "RD06", "desc": "Flat"},
    {"address": "39, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH", "classification": "RD06", "desc": "Flat"},
    {"address": "11, FARMAN ROAD, COVENTRY, CV5 6HP", "classification": "RD04", "desc": "Terraced"},
    {"address": "14, MEADOW STREET, COVENTRY, CV1 3LW", "classification": "RD06", "desc": "Flat"},
    {"address": "1, MERIDEN STREET, COVENTRY, CV1 4DL", "classification": "RH01", "desc": "HMO Parent"},
    {"address": "54, NORTHUMBERLAND ROAD, COVENTRY, CV1 3AQ", "classification": "RD04", "desc": "Terraced"},
    {"address": "14, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH", "classification": "RD06", "desc": "Flat"},
    {"address": "37, CRAVEN STREET, COVENTRY, CV5 8DS", "classification": "RH03", "desc": "HMO Not Further Divided"},
    {"address": "29, RUSHMOOR DRIVE, COVENTRY, CV5 8NL", "classification": "RD06", "desc": "Flat"},
    {"address": "29, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH", "classification": "RD06", "desc": "Flat"},
    {"address": "36A, FARMAN ROAD, COVENTRY, CV5 6HQ", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 25, KERRY HOUSE, WINDSOR STREET, COVENTRY, CV1 3DJ", "classification": "RD06", "desc": "Flat"},
    {"address": "14, BOWLS COURT, COVENTRY, CV5 8PG", "classification": "RD06", "desc": "Flat"},
    {"address": "16, KILBURN DRIVE, COVENTRY, CV5 8NN", "classification": "RD03", "desc": "Semi-Detached"},
    {"address": "198, SOVEREIGN ROAD, COVENTRY, CV5 6LU", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 1-7, 62, BROOMFIELD PLACE, COVENTRY, CV5 6GZ", "classification": "RD06", "desc": "Flat"},
    {"address": "64, MELBOURNE ROAD, COVENTRY, CV5 6JP", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 33, GEORGE POOLE HOUSE, WINDSOR STREET, COVENTRY, CV1 3HJ", "classification": "RD06", "desc": "Flat"},
    {"address": "65, RUSHMOOR DRIVE, COVENTRY, CV5 8NL", "classification": "RD04", "desc": "Terraced"},
    {"address": "164, SOVEREIGN ROAD, COVENTRY, CV5 6LU", "classification": "RD04", "desc": "Terraced"},
    {"address": "106, WAVELEY ROAD, COVENTRY, CV1 3PH", "classification": "RD04", "desc": "Terraced"},
    {"address": "5, ST. THOMAS COURT, BUTTS, COVENTRY, CV1 3GH", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 7, FREMINGTON COURT, 2, UPPER YORK STREET, COVENTRY, CV1 3GQ", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 5, 31-33, ALLESLEY OLD ROAD, COVENTRY, CV5 8BU", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 1, CORRIE HOUSE, THOMAS STREET, COVENTRY, CV1 3ER", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 55, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LJ", "classification": "RD04", "desc": "Terraced"},
    {"address": "106, NORTHUMBERLAND ROAD, COVENTRY, CV1 3PF", "classification": "RD03", "desc": "Semi-Detached"},
    {"address": "69, RUSHMOOR DRIVE, COVENTRY, CV5 8NL", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 32, COMPASS COURT, NORFOLK STREET, COVENTRY, CV1 3LL", "classification": "RD04", "desc": "Terraced"},
    {"address": "APARTMENT 145, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LF", "classification": "RD06", "desc": "Flat"},
    {"address": "17, CUMBRIA CLOSE, COVENTRY, CV1 3PG", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 117, MEADOW HOUSE, UPPER SPON STREET, COVENTRY, CV1 3BG", "classification": "RD06", "desc": "Flat"},
    {"address": "R O S E COMMUNITY CENTRE, HOPE STREET, COVENTRY, CV1 3LH", "classification": "CC08", "desc": "Community Service Centre"},
    {"address": "ALWAR INTERNATIONAL LTD, ARGYLE HOUSE, COLLINGWOOD ROAD, COVENTRY, CV5 6HW", "classification": "CI01", "desc": "Factory/Manufacturing"},
    {"address": "15, COUNDON ROAD, COVENTRY, CV1 4AR", "classification": "RH01", "desc": "HMO Parent"},
    {"address": "15, LUDLOW ROAD, COVENTRY, CV5 6JA", "classification": "RD04", "desc": "Terraced"},
    {"address": "128, SOVEREIGN ROAD, COVENTRY, CV5 6JD", "classification": "RD04", "desc": "Terraced"},
    {"address": "FLAT 33, 57, BUTTS, COVENTRY, CV1 3BJ", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 614, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6NA", "classification": "RD06", "desc": "Flat"},
    {"address": "APARTMENT 407, EARLSDON PARK RETIREMENT VILLAGE, ALBANY ROAD, COVENTRY, CV5 6LZ", "classification": "RD06", "desc": "Flat"},
    {"address": "FLAT 45, GEORGE POOLE HOUSE, WINDSOR STREET, COVENTRY, CV1 3HJ", "classification": "RD06", "desc": "Flat"},
    {"address": "9, CRICKET CLOSE, COVENTRY, CV5 8PQ", "classification": "RD03", "desc": "Semi-Detached"},
    {"address": "6, FARMAN ROAD, COVENTRY, CV5 6HQ", "classification": "RD04", "desc": "Terraced"},
    {"address": "71, KIRBY ROAD, COVENTRY, CV5 6HL", "classification": "RD04", "desc": "Terraced"},
    {"address": "25, SPON END, COVENTRY, CV1 3HB", "classification": "RD04", "desc": "Terraced"},  # dupe
    {"address": "ROOM 29, KOCO BUILDINGS, ARCHES INDUSTRIAL ESTATE, SPON END, COVENTRY, CV1 3JQ", "classification": "CI", "desc": "Industrial"},
    {"address": "FLAT 40, FREMINGTON COURT, 2, UPPER YORK STREET, COVENTRY, CV1 3GQ", "classification": "RD06", "desc": "Flat"},
    {"address": "2, COLLINGWOOD ROAD, COVENTRY, CV5 6HW", "classification": "RD04", "desc": "Terraced"},
]

all_data = hb_data + bbox_data

# Extract road name from address
import re
from collections import defaultdict

def get_road(addr):
    # Normalise known complex addresses
    road_map = {
        "ALBANY ROAD": "ALBANY ROAD",
        "NORFOLK STREET": "NORFOLK STREET",
        "WINDSOR STREET": "WINDSOR STREET",
        "MEADOW STREET": "MEADOW STREET",
        "UPPER SPON STREET": "UPPER SPON STREET",
        "UPPER YORK STREET": "UPPER YORK STREET",
        "THOMAS STREET": "THOMAS STREET",
        "HOPE STREET": "HOPE STREET",
        "GORDON STREET": "GORDON STREET",
        "SPON END": "SPON END",
    }
    for road in road_map:
        if road in addr:
            return road_map[road]
    
    # Try to extract road from address pattern: number, ROAD NAME, COVENTRY
    parts = addr.split(", COVENTRY")[0].split(", ")
    # Road name is typically the second-to-last part before COVENTRY
    for p in reversed(parts):
        p = p.strip()
        if any(p.endswith(s) for s in [" ROAD", " STREET", " LANE", " DRIVE", " CLOSE", " COURT", " PLACE", " GARDENS", " END", " TERRACE"]):
            return p
        if p in ["BUTTS"]:
            return p
    # fallback
    if len(parts) >= 2:
        return parts[-1].strip()
    return parts[0].strip()

roads = defaultdict(lambda: {"count": 0, "types": defaultdict(int)})

seen_uprns = set()
for item in all_data:
    addr = item["address"]
    # Skip exact duplicates
    key = addr
    if key in seen_uprns:
        continue
    seen_uprns.add(key)
    
    road = get_road(addr)
    roads[road]["count"] += 1
    roads[road]["types"][item["desc"]] += 1

# Sort by count descending
sorted_roads = sorted(roads.items(), key=lambda x: -x[1]["count"])

print(f"{'Road Name':<30} {'UPRNs':>6}  Types")
print("-" * 90)
for road, data in sorted_roads:
    types_str = ", ".join(f"{v}× {k}" for k, v in sorted(data["types"].items(), key=lambda x: -x[1]))
    print(f"{road:<30} {data['count']:>6}  {types_str}")

print(f"\n{'TOTAL':<30} {sum(d['count'] for _, d in sorted_roads):>6}")
PYEOF
python3 /home/claude/compile.py
Output

Road Name                       UPRNs  Types
------------------------------------------------------------------------------------------
SPON END                           17  11× Terraced, 2× Shop / Showroom, 1× Workshop / Light Industrial, 1× Church, 1× Public House / Bar / Nightclub, 1× Industrial
ALBANY ROAD                        14  14× Flat
BUTTS                               7  7× Flat
WINDSOR STREET                      7  6× Flat, 1× Terraced
SOVEREIGN ROAD                      7  7× Terraced
FARMAN ROAD                         5  4× Terraced, 1× Flat
COLLINGWOOD ROAD                    4  3× Terraced, 1× Factory/Manufacturing
NORFOLK STREET                      4  4× Terraced
MELBOURNE ROAD                      4  3× Terraced, 1× Shop / Showroom
MEADOW STREET                       3  2× Flat, 1× Terraced
UPPER YORK STREET                   3  3× Flat
RUSHMOOR DRIVE                      3  2× Terraced, 1× Flat
CHESTER STREET                      2  1× HMO Parent, 1× Terraced
KIRBY ROAD                          2  2× Terraced
HOLYHEAD ROAD                       2  1× Flat, 1× Terraced
LUDLOW ROAD                         2  2× Terraced
KILBURN DRIVE                       2  1× Flat, 1× Semi-Detached
CRAVEN STREET                       2  1× Terraced, 1× HMO Not Further Divided
MELVILLE ROAD                       2  1× Terraced, 1× Flat
WAVELEY ROAD                        2  2× Terraced
UPPER SPON STREET                   2  2× Flat
NORTHUMBERLAND ROAD                 2  1× Terraced, 1× Semi-Detached
WELLINGTON GARDENS                  1  1× Terraced
MINSTER ROAD                        1  1× Flat
KINGSTON ROAD                       1  1× HMO Not Further Divided
GORDON STREET                       1  1× HMO Not Further Divided
GLOUCESTER STREET                   1  1× Terraced
HEARSALL LANE                       1  1× Flat
MERIDEN STREET                      1  1× HMO Parent
BOWLS COURT                         1  1× Flat
BROOMFIELD PLACE                    1  1× Flat
ALLESLEY OLD ROAD                   1  1× Flat
THOMAS STREET                       1  1× Flat
CUMBRIA CLOSE                       1  1× Terraced
HOPE STREET                         1  1× Community Service Centre
COUNDON ROAD                        1  1× HMO Parent
CRICKET CLOSE                       1  1× Semi-Detached

TOTAL                             113
Good, clean output. Let me present this nicely.

Done
Here's the breakdown — 113 UPRNs across 37 roads from the sampled area around CV1 3HB:

Road Name	UPRNs	Types
Spon End	17	11 Terraced, 2 Shop/Showroom, 1 Workshop, 1 Church, 1 Pub, 1 Industrial
Albany Road	14	14 Flat (Earlsdon Park retirement village)
Butts	7	7 Flat (at 57 Butts & St Thomas Court)
Windsor Street	7	6 Flat, 1 Terraced (George Poole House, Kerry House, Trafalgar House)
Sovereign Road	7	7 Terraced
Farman Road	5	4 Terraced, 1 Flat
Collingwood Road	4	3 Terraced, 1 Factory/Manufacturing
Norfolk Street	4	4 Terraced (Compass Court)
Melbourne Road	4	3 Terraced, 1 Shop/Showroom
Meadow Street	3	2 Flat, 1 Terraced (Winslow House, Watchmakers Court)
Upper York Street	3	3 Flat (Fremington Court)
Rushmoor Drive	3	2 Terraced, 1 Flat
Chester Street	2	1 HMO, 1 Terraced
Kirby Road	2	2 Terraced
Holyhead Road	2	1 Flat, 1 Terraced
Ludlow Road	2	2 Terraced
Kilburn Drive	2	1 Flat, 1 Semi-Detached
Craven Street	2	1 Terraced, 1 HMO
Melville Road	2	1 Terraced, 1 Flat
Waveley Road	2	2 Terraced
Upper Spon Street	2	2 Flat (Meadow House)
Northumberland Road	2	1 Terraced, 1 Semi-Detached
+ 15 more roads	1 each	Various single UPRNs
Note this is a sample from the OS Places bounding box query (which returns a random subset, not exhaustive). The actual UPRN counts per road will be much higher — for instance Spon End alone likely has 100+ UPRNs. Want me to do a more exhaustive query for specific roads or the full area?

Can you give the size of the bounding box and then produce an excel workbook keyed on road names that accurately gives a breakdown of UPRNs on each road by type. Classify roads as within the bbox or crossing the bbox boundary so we can see which are partial reports of premises count

10:55

Architected Excel workbook with bbox classification and UPRN breakdown
The user wants me to:

Calculate the bounding box size
Create an Excel workbook with road-level UPRN breakdowns by type
Classify roads as "within" or "crossing" the bbox boundary
The bbox I used was [-1.533, 52.404, -1.52, 52.412]. Let me calculate the size and then build a proper Excel file.

For classifying roads as within/crossing the boundary, I'll need to check if the addresses for each road are all well within the bbox or if some appear near the edges (suggesting the road continues beyond).

Let me read the xlsx skill first, then build this.

Show more

Read xlsx skill for best practices
Now let me build the Excel workbook. I need to:

Calculate bbox dimensions
For each road, determine if it's fully within or crossing the bbox boundary by checking if any addresses are near the edges
Create a proper Excel workbook with openpyxl
The bbox was [-1.533, 52.404, -1.52, 52.412]. Let me calculate the approximate size in metres.

Done
Now let me build the workbook with accurate bbox sizing and road classification.


Acknowledged request for spatial analysis and data compilation

Build Excel workbook with road-level UPRN breakdown

Script
Now recalculate formulas.


Recalculate formulas

Script
Let me try a different approach for the recalc script.


Recalculate formulas
bash

cd /mnt/skills/public/xlsx && python3 scripts/recalc.py /mnt/user-data/outputs/cv1_3hb_road_uprns.xlsx 30
Output

{
  "status": "success",
  "total_errors": 0,
  "error_summary": {},
  "total_formulas": 13
}
All formulas calculated successfully. Let me present the file.


Presented file
Done.

Done
The bounding box is 883m × 891m = 78.6 hectares (0.079 km²).

The workbook has three sheets:

Bounding Box Info — dimensions, coordinates, and methodology notes
Roads by Type — 37 roads with UPRN counts broken down by property type (Terraced, Flat, Semi-Detached, HMO, Shop/Showroom, etc.). Each road is colour-coded green (Within) or amber (Boundary)
Classification Codes — same breakdown but using the raw OS classification codes (RD04, RD06, CI01, etc.)
20 roads are classified as fully within the bbox, and 17 roads cross the boundary — meaning their UPRN counts are definitely partial. Note that even "within" roads are sampled rather than exhaustive, since the OS Places bbox query returns a random subset. Spon End at 17 UPRNs is the largest in the sample but in reality will have considerably more.

Cv1 3hb road uprns
Spreadsheet · XLSX 




Claude is AI and can make mistakes. Please double-check responses.