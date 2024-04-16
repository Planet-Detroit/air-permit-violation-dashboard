#!/usr/bin/env python
# coding: utf-8

# # Imports

from io import BytesIO
import pandas as pd
import re
import pdfplumber
import requests
from time import sleep
from pytz import timezone
from datetime import datetime
from ast import literal_eval
import json
import sys
import os
import wget


# # What day is it?

tz = timezone('America/Detroit')
today = datetime.now(tz)
today = today.strftime("%Y-%m-%d")


# # Look for new violations

# Reading in the old parser report:
old_report = pd.read_csv('output/report-parser.csv')

# Reading in the documents from the past 90 days
docs = pd.read_csv('https://raw.githubusercontent.com/srjouppi/michigan-egle-database-auto-scraper/main/output/EGLE-AQD-document-dataset-90days.csv')

# Reading in the dataset of already parsed violation notices
parsed_vn = pd.read_csv('output/EGLE-AQD-Violation-Notices-2018-Present.csv')

# Creating a new dataframe of violation notices whose URLs are not in the parsed violation notices
new_vn = docs.query('(type_simple == "VN") & (~doc_url.isin(@parsed_vn.doc_url))')

#Creating a dictionary for this scrape that will be added to the
#scraper report
one_parse = []
data = {}

data['date'] = pd.to_datetime(today)
data['vns_found'] = len(new_vn)

# # If there are no new violation notices, break the script

if len(new_vn) == 0:
    one_parse.append(data)
    one_parse_df = pd.DataFrame(one_parse)
    
    new_report = pd.concat([old_report,one_parse_df])
    new_report.date = pd.to_datetime(new_report.date)
    new_report.sort_values('date',ascending=False).to_csv('output/report-parser.csv',index=False)
    sys.exit()
    
# # Parse the new PDFs

# Creating the new parsed violation dataframe
new_parsed_vns = pd.DataFrame(columns=['doc_url','location','process_description','rule_permit_condition_violated','comments','full_text','pdf_parsing_error','empty_pdf_error','table_error','flag','comments_found'])

# Looping through the Document URLs
for file in new_vn.doc_url:
    # Download the PDF and save it for posterity
    wget.download(file, out='archive/')

    # Making a list and a dictionary to create a dataframe later on
    one_vn_list = []
    one_vn = {}
    
    # Create a column for doc url and date parsed
    one_vn['doc_url'] = file
    one_vn['date_parsed'] = today
    
    # Try to get the document into pdfplumber
    try:
        # Requesting the file from the URL
        rq = requests.get(file)
        
        # Opening it with PDF plumber
        pdf = pdfplumber.open(BytesIO(rq.content))
        
        # Try to get text from the first page
        try:
            first_page = pdf.pages[0].extract_text().replace('\n',' ')
            # Try to find a location
            try:
                query = r"(?:located\sat\s)(.*, Michigan)"
                match = re.findall(query, first_page)
                
                # If you've got a match, save it:
                if len(match) > 0:
                    one_vn['location'] = match[0]
                else:
                    one_vn['location'] = None
            
            # If you can't, just save an empty column
            except:
                one_vn['location'] = None
                
        # If you can't, it's probably because the page is an image not a true PDF
        # Flagging the parsing error
        
        except:            
            # Saving a PDF error and telling folks to look at the PDF
            one_vn['pdf_parsing_error'] = 1
            unparsable_pdfs = unparsable_pdfs + 1
            
            one_vn['comments'] = "Please see document."
        
            # Making a dataframe with NO COMMENTS in the comments section
            one_vn_list.append(one_vn)
            one_vn_df = pd.DataFrame(one_vn_list)
            
            # Adding it to the main dataframe
            new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df],ignore_index=True)
            
            # Move on to the next file
            continue
        
        # Try to get the text from all pages
        full_text = ''
        try:
            # For every page there is in the pdf
            for page in pdf.pages:
                
                # extract the text and add it to the 'full_text'
                full_text = full_text + page.extract_text()
            
            # After that's finished, save the full_text to the column
            one_vn['full_text'] = full_text
            
        # If that doesn't work, something is probably wrong with the PDF
        except:
            # Saving a PDF error and telling folks to look at the PDF
            one_vn['pdf_parsing_error'] = 1
            unparsable_pdfs = unparsable_pdfs + 1
            one_vn['comments'] = "Please see document."
            
            # Making a dataframe with NO COMMENTS in the comments section
            one_vn_list.append(one_vn)
            one_vn_df = pd.DataFrame(one_vn_list)
            
            # Adding it to the main dataframe
            new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df],ignore_index=True)
            
            # Moving on to the next file
            continue
            
        # Now to extract some comments about what the violation is regarding.
        # Let's rule out some common things first:
        # Look for the common "filure to submit air pollution report" phrasing
        
        query1 = r"\d{4} air pollution report"
        query2 = r"[^.]* AQD has not received [^.]*I?n?c?\.?C?o?r?p?\.?[^.]*\."
        query3 = r"[^.]* after the submittal deadline [^.]*\. As a result[^.]*\."
        
        match1 = re.findall(query1, full_text, re.IGNORECASE)
        match2 = re.findall(query2, full_text, re.IGNORECASE)
        match3 = re.findall(query3, full_text, re.IGNORECASE)
        
        
        # If the text has "SECOND VIOLATION" in it:
        if "SECOND VIOLATION" in full_text:
            one_vn['comments'] = "Second Violation Notice"
            one_vn['comments_found'] = 1
            
            # Making a dataframe with "Second Violation Notice" in comments section
            one_vn_list.append(one_vn)
            one_vn_df = pd.DataFrame(one_vn_list)
            
            # Saving it to the main dataframe
            new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df], ignore_index=True)
            
            # Moving on to the next file
            continue
        
        # If not, then look for the "failure to submit" language
        # If found, save that language to the comments and skip to the next file
        elif len(match1) > 0:
            one_vn['comments'] = f"Failure to submit {match1[0]}"
            one_vn['comments_found'] = 1
            
            # Making a dataframe WITH COMMENTS in comments section
            one_vn_list.append(one_vn)
            one_vn_df = pd.DataFrame(one_vn_list)
            
            # Saving it to the main dataframe
            new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df])
            
            # Moving on to the next file
            continue
            
        elif len(match2) > 0:
            one_vn['comments'] = match2[0]
            one_vn['comments_found'] = 1
            
            # Making a dataframe WITH COMMENTS in comments section
            one_vn_list.append(one_vn)
            one_vn_df = pd.DataFrame(one_vn_list)
            
            # Saving it to the main dataframe
            new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df])
            
            # Moving on to the next file
            continue
        
        elif len(match3) > 0:
            one_vn['comments'] = match3[0]
            one_vn['comments_found'] = 1
            
            # Making a dataframe WITH COMMENTS in comments section
            one_vn_list.append(one_vn)
            one_vn_df = pd.DataFrame(one_vn_list)
            
            # Saving it to the main dataframe
            new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df])
            
            # Moving on to the next file
            continue

        else:
        # If not, then try to extract a table from the first page
        
            try:
                # Creating an empty list of tables:
                table_list = []

                # Looking in the first two pages for tables
                for page in pdf.pages[:2]:
                    table = page.extract_table()

                    # If the table is not None, add it to the list:
                    if table != None:
                        table_list.append(table)
                
                # How long is my list of tables?
                n = len(table_list)

                # If it's empty:
                    #1. Write "please see document" in comments column
                    #2. Make a dataframe and concat it to the main dataframe
                    #3. Move on to the next file

                if n == 0:
                    one_vn['comments'] = 'Please see document.'
                    one_vn['table_error'] = 1
                    one_vn_list.append(one_vn)
                    one_vn_df = pd.DataFrame(one_vn_list)

                    new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df],ignore_index=True)
                    continue

                # If it's not empty:
                else:
                    # Flatten the list of tables
                    flat_list = [item for sublist in table_list for item in sublist]

                    # If there are 3 items in the list, meaning 3 columns:
                    if len(flat_list[0]) == 3:

                        # Look for 'comments' and 'violated' to indicate if we found a violation
                        comments = '?'
                        violation = '?'

                        # For each item in that list
                        for item in flat_list[0]:

                            # If it's not None:
                            if item != None:

                                #Look for comments
                                query4 = r"(comments)"
                                match4 = re.findall(query4, item, re.IGNORECASE)

                                query5 = r"(violated)"
                                match5 = re.findall(query5, item, re.IGNORECASE)

                            if len(match4) > 0:
                                comments = 'yes'
                                continue


                            elif len(match5) > 0:
                                violation = 'yes'
                                continue
        
                        # If we did find comments, save the table as a dataframe
                        if comments == 'yes':
                            comments_df = pd.DataFrame(flat_list,columns=['process_description','rule_permit_condition_violated','comments'])

                            # if 'Comments' is in the first row, save the df without the first row
                            if len(comments_df[:1].query("comments.str.contains('comments',case=False,na=False)")) == 1:
                                comments_df = comments_df[1:]

                            comments_df['doc_url'] = file

                            # Make my list of dictionaries and turn it into a dataframe
                            one_vn['comments_found'] = 1
                            one_vn_list.append(one_vn)
                            one_vn_df = pd.DataFrame(one_vn_list)

                            # Merge dataframe with comments
                            one_vn_df = one_vn_df.merge(comments_df,how='outer',left_on='doc_url',right_on='doc_url')

                        elif violation == 'yes':
                            comments_df = pd.DataFrame(flat_list,columns=['process_description','rule_permit_condition_violated','comments'])

                            #Getting rid of nulls
                            comments_df = comments_df.query('~comments.isnull()')

                            #Adding a disclaimer row
                            disclaimer_df = pd.DataFrame([[None,None,'Please see document.']], columns=['process_description','rule_permit_condition_violated','comments'])
                            comments_df = pd.concat([comments_df,disclaimer_df],ignore_index=True)

                            comments_df['doc_url'] = file
                            comments_df['flag'] = 1

                            # Make my list of dictionaries and turn it into a dataframe
                            one_vn['comments_found'] = 1
                            one_vn_list.append(one_vn)
                            one_vn_df = pd.DataFrame(one_vn_list)

                            # Merge dataframe with comments
                            one_vn_df = one_vn_df.merge(comments_df,how='outer',left_on='doc_url',right_on='doc_url')

                        else:
                            one_vn['comments'] = 'Please see document.'
                            one_vn['table_error'] = 1

                            # Make my list of dictionaries and turn it into a dataframe
                            one_vn_list.append(one_vn)
                            one_vn_df = pd.DataFrame(one_vn_list)
                            
                    else:
                        one_vn['table_error'] = 1
                        one_vn['comments'] = 'Please see document.'

                        # Make my list of dictionaries and turn it into a dataframe
                        one_vn_list.append(one_vn)
                        one_vn_df = pd.DataFrame(one_vn_list)
                        print('adding it to a dataframe WITHOUT comments')
            except:
                one_vn['table_error'] = 1
                one_vn['comments'] = 'Please see document.'
                
                # Make my list of dictionaries and turn it into a dataframe
                one_vn_list.append(one_vn)
                one_vn_df = pd.DataFrame(one_vn_list)
                
    # If that doesn't work
    except:
        # Saving a PDF error and telling folks something went wrong with the PDF
        one_vn['empty_pdf_error'] = 1
        one_vn['comments'] = "An error occured with this PDF. Please reach out to <a class='article' href='https://www.michigan.gov/egle/about/organization/public-information' target='_blank'>EGLE's public information office.</a>"
        
        # Making a dataframe WITH AN ERROR in the comments section
        one_vn_list.append(one_vn)
        one_vn_df = pd.DataFrame(one_vn_list)
    
    # Add this violation dataframe to the larger dataframe
    new_parsed_vns = pd.concat([new_parsed_vns,one_vn_df],ignore_index=True)
    
    # Shhh... sleep...
    sleep(1)


# # Let's save the raw output for posterity:

# Filling the nulls in the error columns with 0
new_parsed_vns[['comments_found','empty_pdf_error','table_error','pdf_parsing_error','flag']] = new_parsed_vns[['comments_found','empty_pdf_error','table_error','pdf_parsing_error','flag']].fillna(0)
old_parsed_vns = pd.read_csv('archive/violations-parsed-raw.csv')

# # Creating a pitstop
# EXPORTING UPDATED RAW PARSED VNS
pd.concat([new_parsed_vns,old_parsed_vns],ignore_index=True).to_csv('archive/violations-parsed-raw.csv',index=False)

# Pivoting the dataframe to get counts of each column
parser_report = new_parsed_vns.pivot_table(index=['doc_url'], values=['comments_found','table_error','pdf_parsing_error','empty_pdf_error','flag'], aggfunc='sum').reset_index()

# # Creating the parser report for the day and saving it
data['comments_found'] = len(parser_report.query('comments_found > 0'))
data['comments_flagged'] = len(parser_report.query('flag > 0'))
data['empty_pdfs'] = parser_report.empty_pdf_error.sum()
data['unparsable_pdfs'] = parser_report.pdf_parsing_error.sum()
data['table_errors'] = len(parser_report.query('(comments_found == 0) & (table_error > 0)'))

one_parse.append(data)
one_parse_df = pd.DataFrame(one_parse)

# EXPORTING UPDATED REPORT
new_report = pd.concat([old_report,one_parse_df])
new_report.date = pd.to_datetime(new_report.date)
new_report.sort_values('date',ascending=False).to_csv('output/report-parser.csv',index=False)

# # Cleaning the output
def process_comments(comments):
    if pd.isnull(comments):
        return "Please see document."
    else:
        return comments.replace("\n", " ")
    
def process_location(location):
    if pd.notnull(location):
        if len(location) < 100:
                return location
        else:
            return None

new_parsed_vns['comments_clean'] = new_parsed_vns.comments.apply(process_comments)
new_parsed_vns['location_clean'] = new_parsed_vns.location.str.split(", Michigan").str[0]
new_parsed_vns['location_clean'] = new_parsed_vns.location_clean.apply(process_location)
new_parsed_vns.full_text = new_parsed_vns.full_text.str.replace("\n"," ")
new_parsed_vns['srn'] = new_parsed_vns.doc_url.str.split('/').str[-1].str.split('_').str[0]

# # For each violation, create a list of comments
file_list = new_parsed_vns.drop_duplicates(subset='doc_url').doc_url.to_list()
files = []

#For each file in the list of files
for file in file_list:
    
    # Make a list of dictionaries for the file:
    one_file = {}
    
    # Filter the dataframe to look at the comments for just that file
    one_file_df = new_parsed_vns.query(f'doc_url == "{file}"')
    
    # Write the HTML to create a list of comments for that file:
    #Opening UL tag
    comment_list = []
    comment_list_html = '<ul>'
    
    # For every comment,
    for index,row in one_file_df.iterrows():
        
        comment = row['comments_clean']
        
        query1 = r"comments"
        query2 = r"comment \d"
       
        match1 = re.findall(query1, comment, re.IGNORECASE)
        match2 = re.findall(query2, comment, re.IGNORECASE)
        if (len(match1) == 0) & (len(match2) == 0):
            
            if comment not in comment_list:
                # Save that comment to a list
                comment_list.append(comment)

                # Save that comment between a list tag
                comment_html = f"<li>{comment}</li>"

                # Add that comment html to a list of comments
                comment_list_html = comment_list_html + comment_html
        
    
    # Close the UL tag
    comment_list_html = comment_list_html + "</ul>"
    
    # Save the filename and the list
    one_file['doc_url'] = file
    one_file['comment_list'] = comment_list
    one_file['comment_list_html'] = comment_list_html
    
    # Add it to my list of dictionaries
    files.append(one_file)
    
    # Create the dataframe
    comments_consolidated = pd.DataFrame(files)

# # Saving cleaned and consolidated parsed vns to new dataframe
# Merging violations parsed with consolidated comments
new_vns_clean = new_parsed_vns.merge(comments_consolidated,how='left',left_on='doc_url',right_on='doc_url').drop_duplicates(subset='doc_url')

# Merging with docs to get doc info:
new_vns_clean = new_vns_clean.merge(docs, how='left',left_on=['doc_url','srn'],right_on=['doc_url','srn'])

# Creating new columns that I'll need later
new_vns_clean['date'] = new_vns_clean.doc_url.str.split('_').str[-1].str.split('.').str[0]
new_vns_clean.date = pd.to_datetime(new_vns_clean.date)
new_vns_clean['date_str'] = new_vns_clean.date.dt.month_name() + " " + new_vns_clean.date.dt.day.astype('str') + ", "  + new_vns_clean.date.dt.year.astype('str')

# Reading in source directory
source_directory = pd.read_csv('docs/EGLE-AQD-source-directory-geocoded.csv')
new_vns_clean = new_vns_clean.merge(source_directory[['srn','lat','long','geometry','facility_name_title','epa_class_full','vn_map_url']], how='left',left_on='srn',right_on='srn')

# Rearranging columns
new_vns_clean = new_vns_clean[['srn','date','date_str','year','facility_name','facility_name_title','epa_class','epa_class_full', 'comment_list', 'comment_list_html', 'county', 'city', 'location_clean','address_full','lat','long','geometry','doc_url','vn_map_url','full_text']]

# # Concatting with old parsed vns and saving
vn_export = pd.concat([new_vns_clean, parsed_vn],ignore_index=True)
vn_export.date = pd.to_datetime(vn_export.date)

print(vn_export.head(6))

# EXPORTING CLEAN PARSED VIOLATION NOTICES
vn_export.to_csv('output/EGLE-AQD-Violation-Notices-2018-Present.csv', index=False)


new_vn_highlight = vn_export.sort_values('date',ascending=False).head(12)
new_vn_highlight.epa_class = new_vn_highlight.epa_class.fillna('None')
def category_color(epa_class):
        if epa_class == "MEGASITE":
            return '#8F0043'
        elif epa_class == "MAJOR":
            return '#FF0037'
        elif epa_class == "SM OPT OUT":
            return '#FF5400'
        elif epa_class == "MINOR":
            return '#FFBD00'
        else:
            return '#DCDCDC'

epa_class_num_dict = {
        'MEGASITE': 1,
        'MAJOR': 2,
        'SM OPT OUT': 3,
        'MINOR': 4,
        'None': 5
    }
new_vn_highlight['properties.county'] = new_vn_highlight.county.str.title()
new_vn_highlight['properties.group_name'] = new_vn_highlight.epa_class_full
new_vn_highlight['properties.group_id'] = new_vn_highlight.epa_class.map(epa_class_num_dict)

# Renaming columns to get ready for geojson
new_vn_highlight = new_vn_highlight.rename({'facility_name_title':'properties.facility_name','geometry':'geometry.coordinates','address_full':'properties.address','date_str':'properties.date_str','date':'properties.date','doc_url':'properties.doc_url','comment_list':'properties.comment_list','comment_list_html':'properties.comment_list_html','srn':'properties.srn','lat':'properties.lat','long':'properties.long'},axis=1)


def list_make(object_list):
    return literal_eval(object_list)

def str_make(object_list):
    return str(object_list)

def process_to_geojson(file):
    geo_data = {"type": "FeatureCollection", "features":[]}
    for row in file:
        this_dict = {"type": "Feature", "properties":{}, "geometry": {}}
        for key, value in row.items():
            key_names = key.split('.')
            if key_names[0] == 'geometry':
                this_dict['geometry'][key_names[1]] = value
            if str(key_names[0]) == 'properties':
                this_dict['properties'][key_names[1]] = value
        geo_data['features'].append(this_dict)
    return geo_data


new_vn_highlight['geometry.coordinates'] = new_vn_highlight['geometry.coordinates'].apply(list_make)
new_vn_highlight['properties.comment_list'] = new_vn_highlight['properties.comment_list'].apply(str_make)
new_vn_highlight['properties.comment_list'] = new_vn_highlight['properties.comment_list'].apply(list_make)

# ### Then create the json file
new_vn_json = json.loads(new_vn_highlight.to_json(orient='records'))
new_vn_geo_format = process_to_geojson(new_vn_json)

#Variable name

with open('output/recent-violations.js', 'w') as outfile:
    outfile.write("var violationData = ")
    
#geojson output
with open('output/recent-violations.js', 'a') as outfile:
    json.dump(new_vn_geo_format, outfile)

# # Creating the map data
# # Reading in my existing map_df and source directory
map_df = pd.read_csv('output/violation-map-data.csv')
# Reading in source violation count table
source_vn_table = pd.read_csv('output/violation-count-by-source.csv')

# # What facilities do I have and which are new?
mapped_facilities = map_df.srn.to_list()
new_facilities = new_vns_clean.query('~srn.isin(@mapped_facilities)').drop_duplicates(subset='srn').srn.to_list()

# # If len(new_facilities) > 0, make an new record in the map_df for the facilit(ies).
if len(new_facilities) > 0:
    for facility in new_facilities:
        if facility not in mapped_facilities:
            new_facility_df = source_directory.query(f'srn == "{facility}"').copy(deep=True)
            new_facility_df['properties.violationCount'] = 0
            new_facility_df['violation_count'] = 0
            new_facility_df[['2018','2019','2020','2021','2022','2023','2024']] = 0
            new_facility_df['type'] = 'Feature'
            new_facility_df['geometry.type'] = 'Point'
            new_facility_df = new_facility_df.rename({'facility_name_title':'properties.facility_name','address_full':'properties.address_full'},axis=1)
            if pd.isnull(new_facility_df.epa_class.item()):
                new_facility_df.epa_class = 'None'
            new_facility_df['properties.group_id'] = new_facility_df.epa_class.replace(epa_class_num_dict)
            new_facility_df['properties.group_name'] = new_facility_df.epa_class_full
            new_facility_df['properties.color'] = new_facility_df.epa_class.apply(category_color)
            new_facility_df['properties.srn'] = new_facility_df.srn
            new_facility_df['properties.violation_article'] = None
            facility_name = new_facility_df.facility_name.item()
            new_facility_df['name_url'] = f"<a href='https://planet-detroit.github.io/air-permit-violation-dashboard/?srn={facility}' target='_blank'>{facility_name}</a>" 
            new_facility_df = new_facility_df.rename({'geometry':'geometry.coordinates'},axis=1)
            # Inserting dummy datetime: 
            new_facility_df['properties.most_recent_vn'] = '1900-01-01'
            new_facility_df['most_recent_vn'] = ''
            map_df = pd.concat([map_df,new_facility_df.drop(['epa_class_simple','epa_class_full','violation_count','most_recent_vn'],axis=1)],ignore_index=True)
            source_vn_table = pd.concat([source_vn_table,new_facility_df[['facility_name','name_url','county','epa_class_simple','srn','violation_count','most_recent_vn']]])
            mapped_facilities.append(facility)

# # Now that there's an entry for every facility, let's start editing the tooltip 
# # and article for the facilities with new violation notices
map_update_report = []

# For every unique facility in the new violation notices:
for facility in new_vns_clean.drop_duplicates(subset='srn').srn:

    # try:
    # Starting a report for this facility being updated
    one_facility_report = {}
    one_facility_report['facility_name'] = map_df.query(f'srn=="{facility}"')['facility_name'].item()
    one_facility_report['address_full'] = map_df.query(f'srn=="{facility}"')['properties.address_full'].item()
    one_facility_report['epa_class'] = map_df.query(f'srn=="{facility}"')['epa_class'].item()
    one_facility_report['srn'] = facility
    one_facility_report['old_violation_count'] = map_df.query(f'srn=="{facility}"')['properties.violationCount'].item()
    one_facility_report['date_updated'] = today

    # Filter the violations down to that facility and order by date
    one_facility_df = new_vns_clean.query(f'srn == "{facility}"').sort_values('date')

    # Get ready to save violation_article
    new_violation_article = ''

    # Get ready to count new violation notices
    new_violation_count = 0

    # Get the most recent vn date
    # Most_recent_vn:
    most_recent_vn_str = map_df.query(f'srn == "{facility}"')['properties.most_recent_vn'].astype('str').item()
    most_recent_vn = pd.to_datetime(most_recent_vn_str)
                                    
    years_updated = []
    # For every record in the filtered df
    for index,row in one_facility_df.iterrows():

        # Increase new violation count by 1 
        new_violation_count = new_violation_count + 1

        # Save the URL, Date, comment_list_html and location as variables 
        url = row['doc_url']
        date_str = row['date_str']
        date = row['date']
        if date > most_recent_vn:
            most_recent_vn = date
            most_recent_vn_str = date.strftime('%Y-%m-%d')
        comment_list_html = row['comment_list_html']
        location = row['location_clean']
        address = row['address_full']
        year = row['date'].year

        # For those that have a location and an address
        if (pd.notnull(location)) & (pd.notnull(address)):

            # If they don't match, include the location in the tooltip
            if (location[:3] != address[:3]):
                text = f"<a href='{url}' target='_blank'>{date_str}</a><img class='icon' src='img/doc-link.svg'/><br><span class='location'><p><span style='font-weight:700;'>Location:</span> {location}</span></p><p>{comment_list_html}</p><br>"
            
            # If they do, skip it
            else:
                text = f"<a href='{url}' target='_blank'>{date_str}</a><img class='icon' src='img/doc-link.svg'/><br><p>{comment_list_html}</p><br>"

        else:
                text = f"<a href='{url}' target='_blank'>{date_str}</a><img class='icon' src='img/doc-link.svg'/><br><p>{comment_list_html}</p><br>"

        # Adding text for this record to the violation_article
        new_violation_article = text + new_violation_article

        # Adding 1 violation to the year
        map_df.loc[map_df.srn == facility,f'{year}'] = new_violation_count + map_df.loc[map_df.srn == facility][f'{year}']

        if year not in years_updated:
            years_updated.append(year)
        # Moving on to the next record

    # I'm all done with this facility so I'm going to update some things for this facility
    # 1. Violation Tooltip
    if facility in new_facilities:
        map_df.loc[map_df.srn == facility,'properties.violation_article'] = new_violation_article
    else:
        map_df.loc[map_df.srn == facility,'properties.violation_article']  = new_violation_article + map_df.loc[map_df.srn == facility]['properties.violation_article']

    # 2. Add to total Violation Count 
    old_violation_count = map_df.loc[map_df.srn == facility]['properties.violationCount'].item()
    updated_violation_count = new_violation_count + old_violation_count
    map_df.loc[map_df.srn == facility,'properties.violationCount'] = updated_violation_count
    source_vn_table.loc[source_vn_table.srn == facility,'violation_count'] = updated_violation_count
    one_facility_report['new_violation_count'] = updated_violation_count


    # 5. Update most_recent_vn:
    map_df.loc[map_df.srn == facility, 'properties.most_recent_vn'] = most_recent_vn_str
    source_vn_table.loc[source_vn_table.srn == facility,'most_recent_vn'] = most_recent_vn_str

    
    # 6. Appending the report
    map_update_report.append(one_facility_report)

# # Creating the map update report to make sure everything is correct!
parser_srn_report = new_vns_clean.srn.value_counts().to_frame().reset_index().rename({'count':'violations_parsed'},axis=1)
map_update_report = pd.DataFrame(map_update_report)


# Merging with parser report to make sure all vns are accounted for
map_update_report = map_update_report.merge(parser_srn_report,how='left',left_on='srn',right_on='srn')
map_update_report.date_updated = pd.to_datetime(map_update_report.date_updated)

# Reading in old map report
old_map_report = pd.read_csv('output/report-map-update.csv')

# EXPORTING MAP UPDATE REPORT
updated_map_report = pd.concat([old_map_report,map_update_report],ignore_index=True)
updated_map_report.date_updated = pd.to_datetime(updated_map_report.date_updated)
updated_map_report.sort_values('date_updated',ascending=False).to_csv('output/report-map-update.csv',index=False)

# Exporting updated map data
map_df.to_csv('output/violation-map-data.csv',index=False)

# Exporting updated source table data
source_vn_table.to_csv('output/violation-count-by-source.csv',index=False)

# # I'm going to turn this map data into a JSON file now!

# Exporting only the files that have geometry
map_df_final = map_df.loc[map_df['geometry.coordinates'].notnull()]
map_df_final['geometry.coordinates'] = map_df_final['geometry.coordinates'].apply(list_make)


# ### Then create the json file
map_df_json = json.loads(map_df_final.to_json(orient='records'))
map_df_geo_format = process_to_geojson(map_df_json)

#Variable name

with open('output/violation-map-geo-data.js', 'w') as outfile:
    outfile.write("var infoData = ")
    
#geojson output
with open('output/violation-map-geo-data.js', 'a') as outfile:
    json.dump(map_df_geo_format, outfile)

# Voila!

