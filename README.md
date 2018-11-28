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
- The first row must contain the field names.  The ordering of the columns does not matter.
- Multiple numbered columns can be used to represent multiple-valued fields.  For example, if there are multiple authors, then add columns called `creator2`, `creator3`, etc.
- Field values are as per the table below:  (Note: more to be added soon)

|Field Name|Required?|Label in GWSS UI (if different)|Notes|
|----------|---------|-------------------------------|-----|
|title1|Y|||
|creator1|Y|Author||
|resource_type1|Y|Type of Work||
|license1|Y|||
|gw_affiliation1|N|GW Unit||
|location1|N|||
|date_created1|N||Should be YYYY format|
|description1|N|Abstract||
|keyword1|N||
|files|Y||Path to the attachment file, or in the case of multiple attachments, to the folder containing the attachment files|
|first_file|N||Path to the file which should be positioned as the first attachment (used for the thumbnail, etc.|
|object_id|N||If specified, the GW ScholarSpace ID of the existing object to be updated|


## Updating existing items

To update items already in GW ScholarSpace, populate the `object_id` column with the GWSS ID of the item.

When updating:

- If a column is left blank, batch loading will _*delete*_ the metadata for that field on the existing item in GWSS.  For instance, if the item in GWSS currently has a "GW Unit" value, then updating it via the batch loader and leaving the `gw_affiliation1` column blank wil _*remove*_ the GW Unit value in GWSS.  If there is no `gw_affiliation1` column in the CSV, then the GW Unit metadata in GWSS will not be modified, if present. 
