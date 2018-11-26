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

    python batch_loader.py <path to csv>


## Specification of CSV
1. The first row must contain the field names.
2. The following columns are required:
   - title1
   - creator1
   - resource_type1
   - license1
   - files - path to the attachment file, or in the case of multiple attachments, to the folder containing the attachment files
   - first_file - (Optional) Path to the file which should be positioned as the first attachment (used for the thumbnail, etc.)
   - object_id - (Optional) If specified, the GW ScholarSpace ID of the existing object to be updated
3. Multiple numbered columns can be used to represent multiple-valued fields.  For example, if there are multiple authors, then add columns called `creator2`, `creator3`, etc.
5. Additional fields included in the CSV will be passed to GWSS using the provided 
   field names. For example, a "subtitle" field included in the CSV will be
   passed as "subtitle" to GWSS.
6. The ordering of columns does not matter.
