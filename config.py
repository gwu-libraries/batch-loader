# GW ScholarSpace ingest configuration
#ingest_path = "/opt/scholarspace/scholarspace-hyrax"
#ingest_command = "rvmsudo RAILS_ENV=production rake gwss:ingest_etd"

#debug_mode = False

# Example for fake_rake:

ingest_path = "example/"
# Command location is relative to ingest path
ingest_command = "python ../fake_rake.py"

debug_mode = True

from configparser import ConfigParser

config=ConfigParser()
#to add more required fields add the name in 'Fields' section , to remove simply delete the value from 'Fields'

#Required_values.ini is dynamically created with write mode and the values are read in the batch_loader program in line #17
#from the Required_values.ini
#To verify which values are being passed to the program check the Required_values.ini file

config['Fields']={
    'files':'1',
    'first_file':'2',
    'resource_type1' : '3',
    'title1' :'4',
    'license1':'5',
    'rights_statement':'6',
    'object_id':'7'
}

with open('./Required_values.ini','w') as f:
    config.write(f)