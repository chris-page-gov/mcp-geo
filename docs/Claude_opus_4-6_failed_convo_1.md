
Use stats routing to allow me to compare life in Leamington Spa and Warwick

13:27

Identified ward codes to enable comparative statistics analysis
The user wants to compare life in Leamington Spa and Warwick using the stats routing tool to figure out the best approach.

M


Os mcp stats routing
Request

{
  "query": "Compare quality of life indicators between Leamington Spa and Warwick including population, employment, health, housing, education"
}
Response

{"query":"Compare quality of life indicators between Leamington Spa and Warwick including population, employment, health, housing, education","provider":"nomis","nomisPreferred":true,"userSelections":{"comparisonLevel":null,"providerPreference":"AUTO"},"reasons":["Matched labour/census keyword(s)."],"matchedPatterns":["\\bemployment\\b"],"matchedLevels":[],"recommendedTool":"nomis.query","comparisonRecommended":true,"nextSteps":[{"tool":"admin_lookup.find_by_name","note":"Use level=WARD to target specific comparison areas."},{"tool":"os_apps.render_statistics_dashboard","note":"Use the dashboard for multi-area comparisons."},{"tool":"nomis.query","note":"Run direct area comparison queries after selecting area codes (avoid unfiltered dataset listing calls)."}],"notes":["If both locations fall under the same local authority, ONS datasets may not differentiate them.","NOMIS is best for labour/census and small-area (OA/LSOA/MSOA) stats.","If dataset discovery is needed, call nomis.datasets with q and limit (for example q='employment', limit=10)."]}
The routing suggests using NOMIS with ward-level comparisons. Let me find the ward codes for Leamington Spa and Warwick, then use the statistics dashboard.

Done
The stats routing recommends NOMIS for this comparison, using ward-level data. Let me find the relevant wards for both towns.


Diagnosed rendering issue and pivoted to direct data comparison
M


Admin lookup find by name
Request

{
  "text": "Leamington",
  "level": "WARD"
}
Response

{"results":[{"id":"E05010687","level":"WARD","name":"Leamington"},{"id":"E05012625","level":"WARD","name":"Leamington Willes"},{"id":"E05012621","level":"WARD","name":"Leamington Brunswick"},{"id":"E05012622","level":"WARD","name":"Leamington Clarendon"},{"id":"E05012624","level":"WARD","name":"Leamington Milverton"},{"id":"E05012623","level":"WARD","name":"Leamington Lillington"}],"count":6,"live":true,"meta":{"match":"contains","levels":["WARD"],"limitPerLevel":null}}
Good, I have multiple Leamington wards. Now let me find Warwick wards.

M


Admin lookup find by name
Request

{
  "level": "WARD",
  "text": "Warwick"
}
Response

{"results":[{"id":"E05000647","level":"WARD","name":"Warwick"},{"id":"E05012628","level":"WARD","name":"Warwick Aylesford"},{"id":"E05012630","level":"WARD","name":"Warwick Saltisford"},{"id":"E05012629","level":"WARD","name":"Warwick Myton & Heathcote"},{"id":"E05012627","level":"WARD","name":"Warwick All Saints & Woodloes"},{"id":"E05005506","level":"WARD","name":"Melton Warwick"}],"count":6,"live":true,"meta":{"match":"contains","levels":["WARD"],"limitPerLevel":null}}
Now I have the ward codes. Let me use the statistics dashboard to compare these areas. I'll pick the core wards for each town - the Leamington wards (excluding the generic E05010687 which might be elsewhere) and the Warwick wards (excluding Melton Warwick).

The dashboard widget might not have rendered properly. Let me try querying NOMIS directly for some key datasets to compare these areas, and present the data.

Done
I've found the wards for both towns. Let me now launch the statistics dashboard to compare them. I'll include the main wards for each town:

M

mcp-geo
The dashboard widget didn't render in this context. Let me pull some key NOMIS datasets directly to build the comparison. I'll start with population and employment data.


Hunted relevant datasets for comparative urban analysis
M


Nomis datasets
Request

{
  "q": "population census 2021",
  "limit": 10
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"population census 2021","limit":10,"returned":0,"total":0,"truncated":false,"datasets":[],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[],"total":0,"returned":0,"truncated":false}}
Let me try broader searches.

M


Nomis datasets
Request

{
  "limit": 10,
  "q": "population"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"population","limit":10,"returned":10,"total":123,"truncated":true,"datasets":[{"id":"NM_100_1","name":"annual population survey - workplace analysis","description":"A workplace based labour market survey. It includes topics such as economic activity, country of birth, occupation, qualification, hours worked etc."},{"id":"NM_1234_1","name":"SH05a - Non-private population - Not hotels - Persons [1961 Census]","description":null},{"id":"NM_1238_1","name":"SH09 - Non-private population - hotels [1961 Census]","description":"Gives population enumerated in hotels split into staff, relatives of staff, resident guests and visitor guests; number of hotels in different size categories."},{"id":"NM_1239_1","name":"SH10 - All non-private [1961 Census]","description":"Shows population enumerated outside private households by sex in quinquennial age groups up to 65 and over."},{"id":"NM_1242_1","name":"SH13 - Age and marital condition by five year age groups [1961 Census]","description":"Gives population by sex and marital condition in quinquennial age-groups."},{"id":"NM_1243_1","name":"SH14 - Single years under 21 [1961 census]","description":"Shows population under 21 by single years of age."},{"id":"NM_1255_1","name":"SH05b - Non-private population - Not hotels - Establishments [1961 Census]","description":null},{"id":"NM_1300_1","name":"WP101EW - Population (Workplace population)","description":null},{"id":"NM_1302_1","name":"WP201EW - Ethnic group (Workplace population)","description":null},{"id":"NM_1303_1","name":"WP203EW - Country of birth (Workplace population)","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_100_1","name":"annual population survey - workplace analysis","description":"A workplace based labour market survey. It includes topics such as economic activity, country of birth, occupation, qualification, hours worked etc."},{"id":"NM_1234_1","name":"SH05a - Non-private population - Not hotels - Persons [1961 Census]","description":null},{"id":"NM_1238_1","name":"SH09 - Non-private population - hotels [1961 Census]","description":"Gives population enumerated in hotels split into staff, relatives of staff, resident guests and visitor guests; number of hotels in different size categories."},{"id":"NM_1239_1","name":"SH10 - All non-private [1961 Census]","description":"Shows population enumerated outside private households by sex in quinquennial age groups up to 65 and over."},{"id":"NM_1242_1","name":"SH13 - Age and marital condition by five year age groups [1961 Census]","description":"Gives population by sex and marital condition in quinquennial age-groups."},{"id":"NM_1243_1","name":"SH14 - Single years under 21 [1961 census]","description":"Shows population under 21 by single years of age."},{"id":"NM_1255_1","name":"SH05b - Non-private population - Not hotels - Establishments [1961 Census]","description":null},{"id":"NM_1300_1","name":"WP101EW - Population (Workplace population)","description":null},{"id":"NM_1302_1","name":"WP201EW - Ethnic group (Workplace population)","description":null},{"id":"NM_1303_1","name":"WP203EW - Country of birth (Workplace population)","description":null}],"total":123,"returned":10,"truncated":true}}
Let me try to search for Census 2021 datasets which would have ward-level data.

M


Nomis datasets
Request

{
  "limit": 15,
  "q": "TS census"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"TS census","limit":15,"returned":0,"total":0,"truncated":false,"datasets":[],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[],"total":0,"returned":0,"truncated":false}}
Let me search more broadly for Census 2021 topics.

M


Nomis datasets
Request

{
  "limit": 15,
  "q": "usual resident"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"usual resident","limit":15,"returned":10,"total":10,"truncated":false,"datasets":[{"id":"NM_1062_1","name":"LC4415EW - Accommodation type by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_1063_1","name":"LC4416EW - Tenure by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_1136_1","name":"DC4415EWla - Accommodation type by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_1137_1","name":"DC4416EWla - Tenure by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_144_1","name":"KS101EW - Usual resident population","description":null},{"id":"NM_158_1","name":"KS101UK - Usual resident population","description":null},{"id":"NM_1634_1","name":"KS001 - Usual resident population","description":null},{"id":"NM_2021_1","name":"TS001 - Number of usual residents in households and communal establishments","description":null},{"id":"NM_2101_1","name":"RM001 - Accommodation type by car or van availability by number of usual residents aged 17 years or over in household","description":null},{"id":"NM_2231_1","name":"RM131 - Tenure by car or van availability by number of usual residents aged 17 or over in household","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_1062_1","name":"LC4415EW - Accommodation type by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_1063_1","name":"LC4416EW - Tenure by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_1136_1","name":"DC4415EWla - Accommodation type by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_1137_1","name":"DC4416EWla - Tenure by car or van availability by number of usual residents aged 17 or over in household","description":null},{"id":"NM_144_1","name":"KS101EW - Usual resident population","description":null},{"id":"NM_158_1","name":"KS101UK - Usual resident population","description":null},{"id":"NM_1634_1","name":"KS001 - Usual resident population","description":null},{"id":"NM_2021_1","name":"TS001 - Number of usual residents in households and communal establishments","description":null},{"id":"NM_2101_1","name":"RM001 - Accommodation type by car or van availability by number of usual residents aged 17 years or over in household","description":null},{"id":"NM_2231_1","name":"RM131 - Tenure by car or van availability by number of usual residents aged 17 or over in household","description":null}],"total":10,"returned":10,"truncated":false}}
Good, NM_2021_1 is TS001 from Census 2021. Let me also find datasets for employment, health, housing, and qualifications. Let me search for a few key Census 2021 topics.

M


Nomis datasets
Request

{
  "limit": 15,
  "q": "TS economic activity"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"TS economic activity","limit":15,"returned":0,"total":0,"truncated":false,"datasets":[],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[],"total":0,"returned":0,"truncated":false}}
Let me try different search terms.

M


Nomis datasets
Request

{
  "limit": 15,
  "q": "economic activity"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"economic activity","limit":15,"returned":15,"total":127,"truncated":true,"datasets":[{"id":"NM_1003_1","name":"LC2603EW - Proficiency in English by economic activity","description":null},{"id":"NM_100_1","name":"annual population survey - workplace analysis","description":"A workplace based labour market survey. It includes topics such as economic activity, country of birth, occupation, qualification, hours worked etc."},{"id":"NM_1010_1","name":"LC6108EW - Economic activity of full-time students by student accommodation","description":null},{"id":"NM_1022_1","name":"LC6210EW - Economic activity by country of birth","description":null},{"id":"NM_1027_1","name":"LC6215EW - Economic activity by passports held","description":null},{"id":"NM_1028_1","name":"LC6401EW - Economic activity by living arrangements","description":null},{"id":"NM_1029_1","name":"LC6601EW - Occupation by economic activity","description":null},{"id":"NM_1030_1","name":"LC6602EW - Industry by economic activity","description":null},{"id":"NM_1032_1","name":"LC6606EW - NS-SeC by economic activity","description":null},{"id":"NM_1043_1","name":"LC5601EW - Highest level of qualification by economic activity","description":null},{"id":"NM_1046_1","name":"LC6107EW - Economic Activity by sex by age","description":null},{"id":"NM_1065_1","name":"LC4609EW - Car or van availability by economic activity","description":null},{"id":"NM_1094_1","name":"LC5605EWls - Highest level of qualification by economic activity by age","description":null},{"id":"NM_1116_1","name":"DC5601EWla - Highest Level of Qualification by Economic Activity by age","description":null},{"id":"NM_1117_1","name":"DC5602EW - Highest level of qualification by economic activity of full-time students","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_1003_1","name":"LC2603EW - Proficiency in English by economic activity","description":null},{"id":"NM_100_1","name":"annual population survey - workplace analysis","description":"A workplace based labour market survey. It includes topics such as economic activity, country of birth, occupation, qualification, hours worked etc."},{"id":"NM_1010_1","name":"LC6108EW - Economic activity of full-time students by student accommodation","description":null},{"id":"NM_1022_1","name":"LC6210EW - Economic activity by country of birth","description":null},{"id":"NM_1027_1","name":"LC6215EW - Economic activity by passports held","description":null},{"id":"NM_1028_1","name":"LC6401EW - Economic activity by living arrangements","description":null},{"id":"NM_1029_1","name":"LC6601EW - Occupation by economic activity","description":null},{"id":"NM_1030_1","name":"LC6602EW - Industry by economic activity","description":null},{"id":"NM_1032_1","name":"LC6606EW - NS-SeC by economic activity","description":null},{"id":"NM_1043_1","name":"LC5601EW - Highest level of qualification by economic activity","description":null},{"id":"NM_1046_1","name":"LC6107EW - Economic Activity by sex by age","description":null},{"id":"NM_1065_1","name":"LC4609EW - Car or van availability by economic activity","description":null},{"id":"NM_1094_1","name":"LC5605EWls - Highest level of qualification by economic activity by age","description":null},{"id":"NM_1116_1","name":"DC5601EWla - Highest Level of Qualification by Economic Activity by age","description":null},{"id":"NM_1117_1","name":"DC5602EW - Highest level of qualification by economic activity of full-time students","description":null}],"total":127,"returned":15,"truncated":true}}
Let me search for Census 2021 specific datasets - they use the TS/RM prefix. Let me search for "TS0" to find them.

M


Nomis datasets
Request

{
  "limit": 25,
  "q": "TS0"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"TS0","limit":25,"returned":25,"total":83,"truncated":true,"datasets":[{"id":"NM_2017_1","name":"TS060A - Industry","description":null},{"id":"NM_2018_1","name":"TS007B - Age by broad age bands","description":null},{"id":"NM_2019_1","name":"TS004A - Country of Birth","description":null},{"id":"NM_2020_1","name":"TS007A - Age by five-year age bands","description":null},{"id":"NM_2021_1","name":"TS001 - Number of usual residents in households and communal establishments","description":null},{"id":"NM_2022_1","name":"TS002 - Legal partnership status","description":null},{"id":"NM_2023_1","name":"TS003 - Household composition","description":null},{"id":"NM_2024_1","name":"TS004 - Country of birth","description":null},{"id":"NM_2025_1","name":"TS005 - Passports held","description":null},{"id":"NM_2026_1","name":"TS006 - Population density","description":null},{"id":"NM_2027_1","name":"TS007 - Age by single year","description":null},{"id":"NM_2028_1","name":"TS008 - Sex","description":null},{"id":"NM_2029_1","name":"TS009 - Sex by single year of age","description":null},{"id":"NM_2030_1","name":"TS010 - Living arrangements","description":null},{"id":"NM_2031_1","name":"TS011 - Households by deprivation dimensions","description":null},{"id":"NM_2032_1","name":"TS012 - Country of birth (detailed)","description":null},{"id":"NM_2033_1","name":"TS013 - Passports held (detailed)","description":null},{"id":"NM_2035_1","name":"TS015 - Year of arrival in UK","description":null},{"id":"NM_2036_1","name":"TS016 - Length of residence","description":null},{"id":"NM_2037_1","name":"TS017 - Household size","description":null},{"id":"NM_2038_1","name":"TS018 - Age of arrival in the UK","description":null},{"id":"NM_2039_1","name":"TS019 - Migrant Indicator","description":null},{"id":"NM_2040_1","name":"TS020 - Number of non-UK short-term residents by sex","description":null},{"id":"NM_2041_1","name":"TS021 - Ethnic group","description":null},{"id":"NM_2042_1","name":"TS023 - Multiple ethnic group","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_2017_1","name":"TS060A - Industry","description":null},{"id":"NM_2018_1","name":"TS007B - Age by broad age bands","description":null},{"id":"NM_2019_1","name":"TS004A - Country of Birth","description":null},{"id":"NM_2020_1","name":"TS007A - Age by five-year age bands","description":null},{"id":"NM_2021_1","name":"TS001 - Number of usual residents in households and communal establishments","description":null},{"id":"NM_2022_1","name":"TS002 - Legal partnership status","description":null},{"id":"NM_2023_1","name":"TS003 - Household composition","description":null},{"id":"NM_2024_1","name":"TS004 - Country of birth","description":null},{"id":"NM_2025_1","name":"TS005 - Passports held","description":null},{"id":"NM_2026_1","name":"TS006 - Population density","description":null},{"id":"NM_2027_1","name":"TS007 - Age by single year","description":null},{"id":"NM_2028_1","name":"TS008 - Sex","description":null},{"id":"NM_2029_1","name":"TS009 - Sex by single year of age","description":null},{"id":"NM_2030_1","name":"TS010 - Living arrangements","description":null},{"id":"NM_2031_1","name":"TS011 - Households by deprivation dimensions","description":null},{"id":"NM_2032_1","name":"TS012 - Country of birth (detailed)","description":null},{"id":"NM_2033_1","name":"TS013 - Passports held (detailed)","description":null},{"id":"NM_2035_1","name":"TS015 - Year of arrival in UK","description":null},{"id":"NM_2036_1","name":"TS016 - Length of residence","description":null},{"id":"NM_2037_1","name":"TS017 - Household size","description":null},{"id":"NM_2038_1","name":"TS018 - Age of arrival in the UK","description":null},{"id":"NM_2039_1","name":"TS019 - Migrant Indicator","description":null},{"id":"NM_2040_1","name":"TS020 - Number of non-UK short-term residents by sex","description":null},{"id":"NM_2041_1","name":"TS021 - Ethnic group","description":null},{"id":"NM_2042_1","name":"TS023 - Multiple ethnic group","description":null}],"total":83,"returned":25,"truncated":true}}
Let me find more Census 2021 datasets - I need health, housing, qualifications, tenure etc.

M


Nomis datasets
Request

{
  "limit": 25,
  "q": "TS0",
  "includeRaw": false
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"TS0","limit":25,"returned":25,"total":83,"truncated":true,"datasets":[{"id":"NM_2017_1","name":"TS060A - Industry","description":null},{"id":"NM_2018_1","name":"TS007B - Age by broad age bands","description":null},{"id":"NM_2019_1","name":"TS004A - Country of Birth","description":null},{"id":"NM_2020_1","name":"TS007A - Age by five-year age bands","description":null},{"id":"NM_2021_1","name":"TS001 - Number of usual residents in households and communal establishments","description":null},{"id":"NM_2022_1","name":"TS002 - Legal partnership status","description":null},{"id":"NM_2023_1","name":"TS003 - Household composition","description":null},{"id":"NM_2024_1","name":"TS004 - Country of birth","description":null},{"id":"NM_2025_1","name":"TS005 - Passports held","description":null},{"id":"NM_2026_1","name":"TS006 - Population density","description":null},{"id":"NM_2027_1","name":"TS007 - Age by single year","description":null},{"id":"NM_2028_1","name":"TS008 - Sex","description":null},{"id":"NM_2029_1","name":"TS009 - Sex by single year of age","description":null},{"id":"NM_2030_1","name":"TS010 - Living arrangements","description":null},{"id":"NM_2031_1","name":"TS011 - Households by deprivation dimensions","description":null},{"id":"NM_2032_1","name":"TS012 - Country of birth (detailed)","description":null},{"id":"NM_2033_1","name":"TS013 - Passports held (detailed)","description":null},{"id":"NM_2035_1","name":"TS015 - Year of arrival in UK","description":null},{"id":"NM_2036_1","name":"TS016 - Length of residence","description":null},{"id":"NM_2037_1","name":"TS017 - Household size","description":null},{"id":"NM_2038_1","name":"TS018 - Age of arrival in the UK","description":null},{"id":"NM_2039_1","name":"TS019 - Migrant Indicator","description":null},{"id":"NM_2040_1","name":"TS020 - Number of non-UK short-term residents by sex","description":null},{"id":"NM_2041_1","name":"TS021 - Ethnic group","description":null},{"id":"NM_2042_1","name":"TS023 - Multiple ethnic group","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_2017_1","name":"TS060A - Industry","description":null},{"id":"NM_2018_1","name":"TS007B - Age by broad age bands","description":null},{"id":"NM_2019_1","name":"TS004A - Country of Birth","description":null},{"id":"NM_2020_1","name":"TS007A - Age by five-year age bands","description":null},{"id":"NM_2021_1","name":"TS001 - Number of usual residents in households and communal establishments","description":null},{"id":"NM_2022_1","name":"TS002 - Legal partnership status","description":null},{"id":"NM_2023_1","name":"TS003 - Household composition","description":null},{"id":"NM_2024_1","name":"TS004 - Country of birth","description":null},{"id":"NM_2025_1","name":"TS005 - Passports held","description":null},{"id":"NM_2026_1","name":"TS006 - Population density","description":null},{"id":"NM_2027_1","name":"TS007 - Age by single year","description":null},{"id":"NM_2028_1","name":"TS008 - Sex","description":null},{"id":"NM_2029_1","name":"TS009 - Sex by single year of age","description":null},{"id":"NM_2030_1","name":"TS010 - Living arrangements","description":null},{"id":"NM_2031_1","name":"TS011 - Households by deprivation dimensions","description":null},{"id":"NM_2032_1","name":"TS012 - Country of birth (detailed)","description":null},{"id":"NM_2033_1","name":"TS013 - Passports held (detailed)","description":null},{"id":"NM_2035_1","name":"TS015 - Year of arrival in UK","description":null},{"id":"NM_2036_1","name":"TS016 - Length of residence","description":null},{"id":"NM_2037_1","name":"TS017 - Household size","description":null},{"id":"NM_2038_1","name":"TS018 - Age of arrival in the UK","description":null},{"id":"NM_2039_1","name":"TS019 - Migrant Indicator","description":null},{"id":"NM_2040_1","name":"TS020 - Number of non-UK short-term residents by sex","description":null},{"id":"NM_2041_1","name":"TS021 - Ethnic group","description":null},{"id":"NM_2042_1","name":"TS023 - Multiple ethnic group","description":null}],"total":83,"returned":25,"truncated":true}}
Let me search for health, tenure, qualifications, and deprivation datasets.

Done
Good, I have the Census 2021 TS series. Let me now query some key "quality of life" datasets across the Leamington and Warwick wards. I'll pull population, deprivation, health, qualifications, tenure, and economic activity data.


Assembled demographic datasets and ward identifiers for comparative analysis
M


Nomis datasets
Request

{
  "limit": 20,
  "q": "general health"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"general health","limit":20,"returned":20,"total":80,"truncated":true,"datasets":[{"id":"NM_1097_1","name":"LC3403EW - General health by long-term health problem or disability by occupancy rating (rooms)","description":null},{"id":"NM_1098_1","name":"LC3404EW - General health by long-term health problem or disability by occupancy rating (bedrooms)","description":null},{"id":"NM_1160_1","name":"DC3403EW - General health by long-term health problem or disability by occupancy rating (rooms) by age","description":null},{"id":"NM_1161_1","name":"DC3404EW - General health by long-term health problem or disability by occupancy rating (bedrooms) by age","description":null},{"id":"NM_1162_1","name":"DC3405EW - General health by long-term health problem or disability by car or van availability by sex","description":null},{"id":"NM_1165_1","name":"DC3409EW - General health by tenure by sex by age","description":null},{"id":"NM_1309_1","name":"WP302EW - General Health (Workplace population)","description":null},{"id":"NM_1362_1","name":"OT302EW - General health (Out of term-time population)","description":null},{"id":"NM_1400_1","name":"LC3406EW - General health by car or van availability by sex","description":null},{"id":"NM_1404_1","name":"LC3409EW - General health by tenure by age","description":null},{"id":"NM_1407_1","name":"LC3307EW - Provision of unpaid care by general health by households with people who have a long-term health problem or disability","description":null},{"id":"NM_1546_1","name":"QS302UK - General health","description":null},{"id":"NM_1645_1","name":"UV020 - General health","description":null},{"id":"NM_1716_1","name":"CS016 - Sex and age by general health and limiting long-term illness","description":null},{"id":"NM_1717_1","name":"CS017 - Tenure and age by general health and limiting long-term illness","description":null},{"id":"NM_1718_1","name":"CS018 - Sex and amenities and central heating by general health and limiting long-term illness","description":null},{"id":"NM_1719_1","name":"CS019 - General health and limiting long-term illness and occupancy rating by age","description":null},{"id":"NM_1722_1","name":"CS022 - Sex and number of cars or vans in household by general health and limiting long-term illness","description":null},{"id":"NM_1723_1","name":"CS023 - Age and general health by NS-Sec","description":null},{"id":"NM_1725_1","name":"CS025 - Sex and age by general health and provision of unpaid care","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_1097_1","name":"LC3403EW - General health by long-term health problem or disability by occupancy rating (rooms)","description":null},{"id":"NM_1098_1","name":"LC3404EW - General health by long-term health problem or disability by occupancy rating (bedrooms)","description":null},{"id":"NM_1160_1","name":"DC3403EW - General health by long-term health problem or disability by occupancy rating (rooms) by age","description":null},{"id":"NM_1161_1","name":"DC3404EW - General health by long-term health problem or disability by occupancy rating (bedrooms) by age","description":null},{"id":"NM_1162_1","name":"DC3405EW - General health by long-term health problem or disability by car or van availability by sex","description":null},{"id":"NM_1165_1","name":"DC3409EW - General health by tenure by sex by age","description":null},{"id":"NM_1309_1","name":"WP302EW - General Health (Workplace population)","description":null},{"id":"NM_1362_1","name":"OT302EW - General health (Out of term-time population)","description":null},{"id":"NM_1400_1","name":"LC3406EW - General health by car or van availability by sex","description":null},{"id":"NM_1404_1","name":"LC3409EW - General health by tenure by age","description":null},{"id":"NM_1407_1","name":"LC3307EW - Provision of unpaid care by general health by households with people who have a long-term health problem or disability","description":null},{"id":"NM_1546_1","name":"QS302UK - General health","description":null},{"id":"NM_1645_1","name":"UV020 - General health","description":null},{"id":"NM_1716_1","name":"CS016 - Sex and age by general health and limiting long-term illness","description":null},{"id":"NM_1717_1","name":"CS017 - Tenure and age by general health and limiting long-term illness","description":null},{"id":"NM_1718_1","name":"CS018 - Sex and amenities and central heating by general health and limiting long-term illness","description":null},{"id":"NM_1719_1","name":"CS019 - General health and limiting long-term illness and occupancy rating by age","description":null},{"id":"NM_1722_1","name":"CS022 - Sex and number of cars or vans in household by general health and limiting long-term illness","description":null},{"id":"NM_1723_1","name":"CS023 - Age and general health by NS-Sec","description":null},{"id":"NM_1725_1","name":"CS025 - Sex and age by general health and provision of unpaid care","description":null}],"total":80,"returned":20,"truncated":true}}
Let me find the Census 2021 versions of health, qualification, and tenure datasets. Let me search for TS03 and TS05 and TS06 which are the Census 2021 topic summaries.

M


Nomis datasets
Request

{
  "limit": 25,
  "q": "TS03"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"TS03","limit":25,"returned":13,"total":13,"truncated":false,"datasets":[{"id":"NM_2049_1","name":"TS030 - Religion","description":null},{"id":"NM_2050_1","name":"TS032 - Welsh language skills (detailed)","description":null},{"id":"NM_2051_1","name":"TS033 - Welsh language skills (speaking)","description":null},{"id":"NM_2052_1","name":"TS034 - Welsh language skills (writing)","description":null},{"id":"NM_2053_1","name":"TS035 - Welsh language skills (reading)","description":null},{"id":"NM_2054_1","name":"TS036 - Welsh language skills (understanding)","description":null},{"id":"NM_2055_1","name":"TS037 - General health","description":null},{"id":"NM_2056_1","name":"TS038 - Disability","description":null},{"id":"NM_2057_1","name":"TS039 - Provision of unpaid care","description":null},{"id":"NM_2092_1","name":"TS037ASP - General health - Age-standardised proportions","description":null},{"id":"NM_2093_1","name":"TS038ASP - Disability - Age-standardised proportions","description":null},{"id":"NM_2094_1","name":"TS039ASP - Provision of unpaid care - Age-standardised proportions","description":null},{"id":"NM_2096_1","name":"TS031 - Religion (detailed)","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_2049_1","name":"TS030 - Religion","description":null},{"id":"NM_2050_1","name":"TS032 - Welsh language skills (detailed)","description":null},{"id":"NM_2051_1","name":"TS033 - Welsh language skills (speaking)","description":null},{"id":"NM_2052_1","name":"TS034 - Welsh language skills (writing)","description":null},{"id":"NM_2053_1","name":"TS035 - Welsh language skills (reading)","description":null},{"id":"NM_2054_1","name":"TS036 - Welsh language skills (understanding)","description":null},{"id":"NM_2055_1","name":"TS037 - General health","description":null},{"id":"NM_2056_1","name":"TS038 - Disability","description":null},{"id":"NM_2057_1","name":"TS039 - Provision of unpaid care","description":null},{"id":"NM_2092_1","name":"TS037ASP - General health - Age-standardised proportions","description":null},{"id":"NM_2093_1","name":"TS038ASP - Disability - Age-standardised proportions","description":null},{"id":"NM_2094_1","name":"TS039ASP - Provision of unpaid care - Age-standardised proportions","description":null},{"id":"NM_2096_1","name":"TS031 - Religion (detailed)","description":null}],"total":13,"returned":13,"truncated":false}}
Now let me find qualifications, tenure, and economic activity Census 2021 datasets.

M


Nomis datasets
Request

{
  "limit": 25,
  "q": "TS05"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"TS05","limit":25,"returned":9,"total":9,"truncated":false,"datasets":[{"id":"NM_2068_1","name":"TS050 - Number of bedrooms","description":null},{"id":"NM_2069_1","name":"TS051 -  Number of rooms","description":null},{"id":"NM_2070_1","name":"TS052 - Occupancy rating for bedrooms","description":null},{"id":"NM_2071_1","name":"TS053 - Occupancy rating for rooms","description":null},{"id":"NM_2072_1","name":"TS054 - Tenure","description":null},{"id":"NM_2073_1","name":"TS055 - Purpose of second address","description":null},{"id":"NM_2074_1","name":"TS056 - Second address indicator","description":null},{"id":"NM_2075_1","name":"TS058 - Distance travelled to work","description":null},{"id":"NM_2076_1","name":"TS059 - Hours worked","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_2068_1","name":"TS050 - Number of bedrooms","description":null},{"id":"NM_2069_1","name":"TS051 -  Number of rooms","description":null},{"id":"NM_2070_1","name":"TS052 - Occupancy rating for bedrooms","description":null},{"id":"NM_2071_1","name":"TS053 - Occupancy rating for rooms","description":null},{"id":"NM_2072_1","name":"TS054 - Tenure","description":null},{"id":"NM_2073_1","name":"TS055 - Purpose of second address","description":null},{"id":"NM_2074_1","name":"TS056 - Second address indicator","description":null},{"id":"NM_2075_1","name":"TS058 - Distance travelled to work","description":null},{"id":"NM_2076_1","name":"TS059 - Hours worked","description":null}],"total":9,"returned":9,"truncated":false}}
Now let me find the qualifications and economic activity datasets.

M


Nomis datasets
Request

{
  "limit": 25,
  "q": "TS06"
}
Response

{"live":true,"dataset":null,"format":"sdmx","query":"TS06","limit":25,"returned":11,"total":11,"truncated":false,"datasets":[{"id":"NM_2017_1","name":"TS060A - Industry","description":null},{"id":"NM_2077_1","name":"TS060 - Industry","description":null},{"id":"NM_2078_1","name":"TS061 - Method used to travel to work","description":null},{"id":"NM_2079_1","name":"TS062 - NS-SeC","description":null},{"id":"NM_2080_1","name":"TS063 - Occupation","description":null},{"id":"NM_2081_1","name":"TS064 - Occupation - minor groups","description":null},{"id":"NM_2082_1","name":"TS065 - Employment history","description":null},{"id":"NM_2083_1","name":"TS066 - Economic activity status","description":null},{"id":"NM_2084_1","name":"TS067 - Highest level of qualification","description":null},{"id":"NM_2085_1","name":"TS068 - Schoolchildren and full-time students","description":null},{"id":"NM_2100_1","name":"TS060NP - Industry - National Parks","description":null}],"hints":["Use nomis.query with a selected dataset id.","Use q to filter dataset discovery before querying."],"data":{"datasets":[{"id":"NM_2017_1","name":"TS060A - Industry","description":null},{"id":"NM_2077_1","name":"TS060 - Industry","description":null},{"id":"NM_2078_1","name":"TS061 - Method used to travel to work","description":null},{"id":"NM_2079_1","name":"TS062 - NS-SeC","description":null},{"id":"NM_2080_1","name":"TS063 - Occupation","description":null},{"id":"NM_2081_1","name":"TS064 - Occupation - minor groups","description":null},{"id":"NM_2082_1","name":"TS065 - Employment history","description":null},{"id":"NM_2083_1","name":"TS066 - Economic activity status","description":null},{"id":"NM_2084_1","name":"TS067 - Highest level of qualification","description":null},{"id":"NM_2085_1","name":"TS068 - Schoolchildren and full-time students","description":null},{"id":"NM_2100_1","name":"TS060NP - Industry - National Parks","description":null}],"total":11,"returned":11,"truncated":false}}
Now I have all the datasets I need. Let me query the key ones for both sets of wards. I'll use these datasets:

NM_2021_1: TS001 - Population
NM_2031_1: TS011 - Deprivation dimensions
NM_2055_1: TS037 - General health
NM_2072_1: TS054 - Tenure
NM_2083_1: TS066 - Economic activity
NM_2084_1: TS067 - Qualifications
The Leamington ward codes are: E05012625, E05012621, E05012622, E05012624, E05012623

The Warwick ward codes are: E05012628, E05012630, E05012629, E05012627

Now I need to set up the NOMIS queries for these wards and understand the right parameters to use at the ward level.

Show less
Done
Now let me query the key Census 2021 datasets for both towns. I'll pull population, deprivation, health, tenure, economic activity, and qualifications.


Pivoted strategy to access census data for town comparison
M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "params": {
    "geography": "E05012625,E05012621,E05012622,E05012624,E05012623,E05012628,E05012630,E05012629,E05012627",
    "select": "geography_name,geography_code,c2021_restype_3_name,obs_value"
  }
}
Error

{"isError":true,"code":"NOMIS_QUERY_ERROR","message":"Query is incomplete"}
Let me check the dataset structure first.

M


Nomis datasets
Request

{
  "dataset": "NM_2021_1"
}
Response

{"live":true,"dataset":"NM_2021_1","format":"sdmx","data":{"structure":{"header":{"id":"NM_2021_1","prepared":"2026-02-06T13:30:57Z","sender":{"contact":{"email":"census.customerservices@ons.gov.uk","name":"Census Customer Services","telephone":"01329 444 972","uri":"http://www.ons.gov.uk/census"},"id":"NOMIS"},"test":"false"},"keyfamilies":{"keyfamily":[{"agencyid":"NOMIS","annotations":{"annotation":[{"annotationtext":"Current (being actively updated)","annotationtitle":"Status"},{"annotationtext":"Residence type,Communal establishment","annotationtitle":"Keywords"},{"annotationtext":"Persons","annotationtitle":"Units"},{"annotationtext":"census_2021_ts","annotationtitle":"contenttype/sources"},{"annotationtext":"oa2021,lsoa2021,msoa2021,la2021,ward2021,oa,msoa,la","annotationtitle":"contenttype/geoglevel"},{"annotationtext":"All usual residents","annotationtitle":"SubDescription"},{"annotationtext":"c2021ts001","annotationtitle":"Mnemonic"},{"annotationtext":"2022-11-02 09:30:00","annotationtitle":"FirstReleased"},{"annotationtext":"2022-11-02 09:30:00","annotationtitle":"LastUpdated"},{"annotationtext":"About this dataset","annotationtitle":"MetadataTitle0"},{"annotationtext":"This dataset provides Census 2021 estimates that classify usual residents in England and Wales by whether they resided in households and communal establishments. The estimates are as at Census Day, 21 March 2021.\n   \n   National Park data are created by plotting unique properties as identified by their Unique Property Reference Number or postcodes into National Park boundaries current at December 2022. This differs from the OA best fit methodology used for other geographic level data.","annotationtitle":"MetadataText0"},{"annotationtext":"Protecting personal data","annotationtitle":"MetadataTitle1"},{"annotationtext":"Sometimes we need to make changes to data if it is possible to identify individuals. This is known as statistical disclosure control. In Census 2021, we:\n\n* Swapped records (targeted record swapping), for example, if a household was likely to be identified in datasets because it has unusual characteristics, we swapped the record with a similar one from a nearby small area. Very unusual households could be swapped with one in a nearby local authority.\n* Added small changes to some counts (cell key perturbation), for example, we might change a count of four to a three or a five. This might make small differences between tables depending on how the data are broken down when we applied perturbation.","annotationtitle":"MetadataText1"},{"annotationtext":2,"annotationtitle":"MetadataCount"}]},"id":"NM_2021_1","components":{"attribute":[{"assignmentstatus":"Mandatory","attachmentlevel":"Observation","codelist":"CL_OBS_STATUS","conceptref":"OBS_STATUS"},{"assignmentstatus":"Conditional","attachmentlevel":"Observation","codelist":"CL_OBS_CONF","conceptref":"OBS_CONF"},{"assignmentstatus":"Conditional","attachmentlevel":"Observation","codelist":"CL_OBS_ROUND","conceptref":"OBS_ROUND"},{"assignmentstatus":"Conditional","attachmentlevel":"Series","codelist":"CL_UNIT_MULT","conceptref":"UNIT_MULTIPLIER"},{"assignmentstatus":"Mandatory","attachmentlevel":"Series","codelist":"CL_TIME_FORMAT","conceptref":"TIME_FORMAT"},{"assignmentstatus":"Mandatory","attachmentlevel":"Series","codelist":"CL_UNIT","conceptref":"UNIT"},{"assignmentstatus":"Mandatory","attachmentlevel":"Series","conceptref":"TITLE_COMPL"}],"dimension":[{"codelist":"CL_2021_1_GEOGRAPHY","conceptref":"GEOGRAPHY"},{"codelist":"CL_2021_1_C2021_RESTYPE_3","conceptref":"C2021_RESTYPE_3"},{"codelist":"CL_2021_1_MEASURES","conceptref":"MEASURES"},{"codelist":"CL_2021_1_FREQ","conceptref":"FREQ","isfrequencydimension":"true"}],"primarymeasure":{"conceptref":"OBS_VALUE"},"timedimension":{"codelist":"CL_2021_1_TIME","conceptref":"TIME"}},"name":{"value":"TS001 - Number of usual residents in households and communal establishments","lang":"en"},"uri":"Nm-2021d1","version":1.0}]},"xmlns":"http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message","common":"http://www.SDMX.org/resources/SDMXML/schemas/v2_0/common","structure":"http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure","xsi":"http://www.w3.org/2001/XMLSchema-instance","schemalocation":"http://sdmx.org/docs/2_0/SDMXMessage.xsd"}}}
I need to query with the right parameters. The dimensions are GEOGRAPHY, C2021_RESTYPE_3, MEASURES, FREQ, and TIME. Let me try querying with JSON-stat format which might be easier.

M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "jsonstat",
  "params": {
    "geography": "E05012625,E05012621,E05012622,E05012624,E05012623,E05012628,E05012630,E05012629,E05012627",
    "c2021_restype_3": "0",
    "measures": "20100",
    "select": "geography_name,geography_code,obs_value"
  }
}
Error

{"isError":true,"code":"NOMIS_QUERY_ERROR","message":"Query is incomplete"}
Let me try a different approach - let me look at what parameters are needed.

M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "jsonstat",
  "params": {
    "geography": "E05012625,E05012621,E05012622,E05012624,E05012623,E05012628,E05012630,E05012629,E05012627",
    "c2021_restype_3": "0",
    "measures": "20100",
    "time": "latest",
    "freq": "a"
  }
}
Error

{"isError":true,"code":"NOMIS_QUERY_ERROR","message":"Query is incomplete"}
Let me try without abbreviating parameters.

M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "jsonstat",
  "params": {
    "geography": "645922049...645922053,645922055...645922058",
    "c2021_restype_3": "0",
    "measures": "20100"
  }
}
Error

{"isError":true,"code":"NOMIS_QUERY_ERROR","message":"Query is incomplete"}
Let me try using TYPE codes instead for ward level geography. Maybe I need to use the ward2021 geography type.

M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "jsonstat",
  "params": {
    "geography": "645922049,645922050,645922051,645922052,645922053,645922055,645922056,645922057,645922058"
  }
}
Error

{"isError":true,"code":"UPSTREAM_INVALID_RESPONSE","message":"NOMIS API returned invalid JSON."}
Let me try a completely different approach - use the NOMIS API conventions. The ward codes like E05012625 should be usable. Maybe I need to query with different ID format. Let me try querying with geography type specification.

M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "jsonstat",
  "params": {
    "geography": "TYPE645",
    "c2021_restype_3": "0",
    "measures": "20100"
  }
}
Error

{"isError":true,"code":"NOMIS_QUERY_ERROR","message":"Query is incomplete"}
I'm struggling with the NOMIS query format. Let me try a different approach - use the nomis_codelists to understand the geography options for this dataset, or try the sdmx format.

M


Nomis codelists
Request

{
  "codelist": "CL_2021_1_GEOGRAPHY",
  "format": "json"
}
Error

{"isError":true,"code":"UPSTREAM_INVALID_RESPONSE","message":"NOMIS API returned invalid JSON."}
Let me try the SDMX format.

M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "sdmx",
  "params": {
    "geography": "645922049",
    "c2021_restype_3": "0",
    "measures": "20100"
  }
}
Error

{"isError":true,"code":"NOMIS_API_ERROR","message":"NOMIS API error: \"{ \\\"error\\\" : \\\"Failed to convert Generic SDMX to JSON\\\" }\""}
I'm having trouble with the NOMIS API formatting. Let me try a completely different approach - instead of NOMIS, let me query ONS directly for these areas, or let me try the nomis query with just a simple geography specification. Actually, let me try building this as a comprehensive HTML-based comparison using search + what I know. Or better yet, let me try a different query parameter approach.

Actually, the issue might be that NOMIS needs numeric IDs, not the E05 codes. Let me try looking up the numeric IDs for these wards.

Actually, looking at the CL_2021_1_GEOGRAPHY codelist - for Census 2021 data, ward codes might use a different format.

Let me start with a single test case to debug this.

Show less
M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "jsonstat",
  "params": {
    "geography": "E05012625"
  }
}
Error

{"isError":true,"code":"NOMIS_QUERY_ERROR","message":"Query is incomplete"}
Let me try using select parameter and different measurement format.

M


Nomis query
Request

{
  "dataset": "NM_2021_1",
  "format": "jsonstat",
  "params": {
    "geography": "E05012625",
    "select": "geography_name,c2021_restype_3_name,obs_value",
    "measures": "20100"
  }
}
Error

{"isError":true,"code":"NOMIS_QUERY_ERROR","message":"Query is incomplete"}
Let me try looking at the nomis_concepts to understand the dimension codes.

M


Nomis concepts
Request

{
  "format": "json"
}
Error

{"isError":true,"code":"UPSTREAM_INVALID_RESPONSE","message":"NOMIS API returned invalid JSON."}
The NOMIS API is being tricky. Let me try a different approach entirely. Instead of fighting with NOMIS API parameters, let me use the ONS data query tool to get census data, or let me build the comparison from web search. Actually, let me try the ONS search for Census 2021 data.

Done
Let me try the ONS API route instead, which may be more straightforward for Census 2021 data.


Pivoted toward direct API integration for comparative statistics



Let me take a more direct approach and fetch the NOMIS data via the API URLs.


Investigated NOMIS query parameters for regional comparison




Claude is AI and can make mistakes. Please double-check responses.
