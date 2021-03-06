# batch-loader
Application for batch loading GW ScholarSpace

## Setup
Requires Python >= 3.5

1. Get this code.

        git clone https://github.com/gwu-libraries/batch-loader.git

2. Create a virtualenv.

        virtualenv -p python3 ENV
        source ENV/bin/activate
    
3. Copy configuration file.

        cp example.config.py config.py
    
4. Edit configuration file. The file is annotated with descriptions of the configuration options.

## Running
To run batch-loader:

    source ENV/bin/activate
    python batch_loader.py <path to csv>


## Specification of CSV

- The first row must contain the field names.  The ordering of the columns does not matter. The batch loader will choke if there are spaces after the field names. Any field names that are not recognized by GWSS will be ignored (note: no error message will be output, and remaining data will be loaded).
- Multiple numbered columns can be used to represent multiple-valued fields.  For example, if there are multiple authors, then add columns called `creator2`, `creator3`, etc.
- The bulk loader doesn't handle diacritics and certain special characters well. It will fail to load any spreadsheet with these characters. These characters can be added back in the GWSS manual editor (via the web admin UI). 
- Field values are as per the table below:  (Note: more to be added soon)

|Field Name|Required?|Label in GWSS UI (if different)|Notes|
|----------|---------|-------------------------------|-----|
|title1|Y|||
|creator1|Y|Author||
|resource_type1|Y|Type of Work|For values, see https://github.com/gwu-libraries/scholarspace-hyrax/blob/master/config/authorities/resource_types.yml|
|license1|Y||For values, see https://github.com/gwu-libraries/scholarspace-hyrax/blob/master/config/authorities/licenses.yml - NOTE: use the `id` values|
|rights_statement|Y||For values, see https://github.com/gwu-libraries/scholarspace-hyrax/blob/master/config/authorities/rights_statements.yml - NOTE: use the `id` values.  Also note that this is a single-valued field.|
|gw_affiliation1|N|GW Unit|For values, see https://github.com/gwu-libraries/scholarspace-hyrax/blob/master/config/authorities/gw_affiliations.yml|
|location1|N|||
|date_created1|N||Should be YYYY format|
|description1|N|Abstract||
|keyword1|N|||
|identifier1|N|||
|contributor1|N|||
|publisher1|N|||
|language1|N|||
|related_url1|N|||
|bibliographic_citation1|N|Previous Publication Information||
|depositor|Y||Email address for the depositor/owner in GWSS|
|files|Y||Path to the attachment file, or in the case of multiple attachments, to the folder containing the attachment files|
|first_file|Y||(Field name is required, value is not) Path to the file which should be positioned as the first attachment (used for the thumbnail, etc.|
|object_id|Y||(Field name is required, value is not) If specified, the GW ScholarSpace ID of the existing object to be updated|


## Updating existing items

To update items already in GW ScholarSpace, populate the `object_id` column with the GWSS ID of the item.

When updating:

- If a column is left blank, batch loading will _*delete*_ the metadata for that field on the existing item in GWSS.  For instance, if the item in GWSS currently has a "GW Unit" value, then updating it via the batch loader and leaving the `gw_affiliation1` column blank wil _*remove*_ the GW Unit value in GWSS.  If there is no `gw_affiliation1` column in the CSV, then the GW Unit metadata in GWSS will not be modified, if present. 
- If `first_file` is left blank, batch loading will _*only*_ update metadata and will not update files.  Any existing file attachments will be left in place.

## Debugging tips

- The batch loader generates a temporary `manifest.json` file, which it then points to when calling the rake task.  However, it normally then deletes `manifest.json` once the load is successful.  For debugging purposes, you'll often want to see this `manifst.json` file.  In `config.py`, set `debug_mode` to `True` and the file won't be deleted.  You can then do things like calling the rake task manually, to see the stack trace thrown by the rake task.
