# Planet Detroit's Dashboard of Michigan Air Permit Violations
-------
This dashboard contains an interactive map of Michigan facilities that have violatated their permits within the past five years, as well as a digest of the most recent violation notices issued by the Michigan Department Environment Great Lakes and Energy (EGLE) that oversees the air quality program.

The map updates daily with new violation notices posted to [EGLE's Air Quality Division database.](https://www.egle.state.mi.us/aps/downloads/srn/)

### How it works
🔍 **Finding and parsing new violation notices** 

A python script looks for new violations added to the EGLE database. [Data and methodology can be found here.](https://www.shelbyjouppi.com/egle-air-database) Using the library [pdfplumber](https://github.com/jsvine/pdfplumber) the script searches for standard phrases and tables that indicate which violations are cited in the notice.



