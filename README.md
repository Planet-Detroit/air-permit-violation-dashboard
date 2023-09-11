# Planet Detroit's Dashboard of Michigan Air Permit Violations
----
#### by [Shelby Jouppi](https://www.shelbyjouppi.com)

This dashboard contains an interactive map of Michigan facilities that have violatated their permits within the past five years, as well as a digest of the most recent violation notices issued by the Michigan Department Environment Great Lakes and Energy (EGLE) that oversees the air quality program.

The map updates daily with new violation notices posted to [EGLE's Air Quality Division database.](https://www.egle.state.mi.us/aps/downloads/srn/)

### How it works
🔍 **Finding and parsing new violation notices** 

A python script looks for new violations added to the EGLE database. [Data and methodology can be found here.](https://www.shelbyjouppi.com/egle-air-database) Using the library [pdfplumber](https://github.com/jsvine/pdfplumber) the script searches for standard phrases and tables that indicate which violations are cited in the notice. It also extracts the full text of the PDF.

:chart_with_upwards_trend: **Clean and save the data**

The script then cleans the violation details and saves it to a csv with the following fields:

:file_fold: `output/EGLE-AQD-Violation-Notices-2018-Present.csv`

| field    | description |
| -------- | ------- |
| srn  | The facility's unique State Registration Number. |
| facility_name | Name of the facility according to this [directory.](https://www.deq.state.mi.us/aps/downloads/SRN/Sources_By_ZIP.pdf) |
| epa_class | The classifcation assigned to the facility by the EPA based on the amount of Hazardous or cumulative air pollutants it emits. In order of severity, the classes are "Megasite", "Major", "Synthetic Minor", "True Minor." |
| date | The date the violation was issued according to EGLE's file naming convention. [Read more](https://shelbyjouppi.com/egle-air-database/)|
| comment_list | A list of comments extracted from the violation table in the notice. If no table was parsed, then it is likely the parser found a boiler plate violation like a "Failure to submit [YEAR] air pollution report" or a "Second violation notice." |
| address_full | The address of the facility according to this [directory.](https://www.deq.state.mi.us/aps/downloads/SRN/Sources_By_ZIP.pdf) |
| location_clean | The location of the violation. Most of the time this matches the address of the facility, but occasionally there are different locations associated with the same SRN.|
| doc_url | The url for the violation notice hosted on EGLE's database. |
| full_text | A raw copy of the entire text of the violation notice as extracted by pdfplumber. |

:round_pushpin: **Update the map with the new violations**

The script then updates the facilities with new violation notices by adding to the total violation count for that facility as well as the year and updating its article with the new violation text.

It then exports another file with the top 6 most recent violation notices to populate the dashboard.

### The files
| file    | description |
| -------- | ------- |
| `EGLE-AQD-violation-parser-mapbuilder.py` | is the python script that runs the violation parser and updates the map with new violations. It runs daily using Github Actions. |

:file_folder: `output/`


| file    | description |
| -------- | ------- |
`EGLE-AQD-Violation-Notices-2018-Present.csv` | Each violation notice issued since 2018 parsed. See details above.|
`violation-map-data.csv` | A .csv version of the data used to populate the map. Each record represents one source.
`violation-map-geo-data.js` | The javascript file used to populate the map.|
`recent-map-violations.js` | The javascript file used to populate the most recent violation notices on the dashboard.|
`map-update-report.csv` | Shows which sources were updated on the map by the script each day. |

:file_folder: `docs/`

| file    | description |
| -------- | ------- |
|`EGLE-AQD-source-directory-geocoded.csv` | A directory of sources with their `epa_class`, `address`, and geocoded (`lat`, `long`) using Google Maps API. This may contain errors, so please [report any issues using this form](LINK!!!!).|
|`violation-map.css` | The stylesheet for the violation dashboard.

:file_folder: `archive/`

| file    | description |
| -------- | ------- |
| `violations-parsed-raw.csv` | A raw copy of the output of the violation parser. One violation notice may have multiple records depending on the number of 'comments' found in the violation table. Novel fields included `process_description` and. `rule_permit_condition_violated.`|
