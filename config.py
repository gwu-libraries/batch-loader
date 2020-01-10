# GW ScholarSpace ingest configuration
#ingest_path = "/opt/scholarspace/scholarspace-hyrax"
#ingest_command = "rvmsudo RAILS_ENV=production rake gwss:ingest_etd"

#debug_mode = False

# Example for fake_rake:

from configparser import ConfigParser

config1=ConfigParser()

ingest_path = "example/ExcelRead.xlsx"
# Command location is relative to ingest path
ingest_command = "python3 ../fake_rake.py"

debug_mode = True


# add required fields as a key:value pair

config1['Fields']={
    'files':'1',
    'resource_type1' : '2',
    'title1' :'3',
    'creator1':'4',
    'license1':'5',
    'rights_statement':'6',
    'object_id':'7'
}

with open('./Required_Values.ini','w') as f:
    config1.write(f)
