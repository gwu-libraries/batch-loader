# GW ScholarSpace ingest configuration
ingest_path = "/opt/scholarspace/scholarspace-hyrax"
ingest_command = "rvmsudo RAILS_ENV=production rake gwss:ingest_etd"
ingest_depositor = "openaccess@gwu.edu"

debug_mode = False

# Example for fake_rake:
"""
ingest_path = "example/"
# Command location is relative to ingest path
ingest_command = "python ../fake_rake.py"
ingest_depositor = "openaccess@gwu.edu"

debug_mode = True
"""
