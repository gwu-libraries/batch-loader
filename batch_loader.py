import argparse
import logging
import csv
import re
import tempfile
import json
import os
import shutil
import subprocess
import get_file
log = logging.getLogger(__name__)

required_field_names = (
    'files',
    'fulltext_url',
    'resource_type1',
    'title1',
    'creator1',
    'license1'
)

def run_ingest_process(csv_path,ingest_command,ingest_path,ingest_depositor,url = None,debug = None ):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO
    )
    logging.basicConfig(level=logging.DEBUG)

    field_names, rows = load_csv(csv_path)
    log.info('Loading {} object from {}'.format(len(rows), csv_path))
    validate_field_names(field_names,url)
    singular_field_names, repeating_field_names = analyze_field_names(field_names)
    base_filepath = os.path.dirname(os.path.abspath(csv_path))
    raw_download_dir = tempfile.mkdtemp()
    for row in rows:
        if url: #boolean if we are using urls to get file or not
            print(row['fulltext_url'])
            file_full_path  = get_file.download_file(row['fulltext_url'],dwnld_dir = raw_download_dir)
            row['files'] = file_full_path
            row['first_file'] = file_full_path
        metadata = create_repository_metadata(row, singular_field_names, repeating_field_names)
        metadata_temp_path = tempfile.mkdtemp()
        metadata_filepath = os.path.join(metadata_temp_path, 'metadata.json')
        try:
            with open(metadata_filepath, 'w') as repo_metadata_file:
                json.dump(metadata, repo_metadata_file, indent=4)
                log.debug('Writing to {}: {}'.format(metadata_filepath, json.dumps(metadata)))
            try:
                first_file, other_files = find_files(row['files'], row.get('first_file'), base_filepath)
                # TODO: Handle passing existing repo id
                repo_id = repo_import(metadata_filepath, metadata['title'], first_file, other_files, None,
                                      ingest_command,
                                      ingest_path,
                                      ingest_depositor)
                # TODO: Write repo id to output CSV
            except Exception as e:
                # TODO: Record exception to output CSV
                raise e
        finally:
            if (not config.debug_mode) and os.path.exists(metadata_filepath):
                shutil.rmtree(metadata_temp_path, ignore_errors=True)
                if os.path.exists(raw_download_dir):
                    shutil.rmtree(raw_download_dir, ignore_errors=True)

def load_csv(filepath):
    """
    Reads CSV and returns field names, rows
    """
    log.debug('Loading csv')
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile)
        return reader.fieldnames, list(reader)


def validate_field_names(field_names,use_url):
    """
    ensures the required fields are present in the data source
    """
    log.debug('Validating field names')
    for field_name in required_field_names:
        if field_name == 'files':
            if use_url:
                continue #we dont need this if we use urls instead
        if field_name == 'fulltext_url':
            if not use_url:
                continue #we dont need this if we have paths instead of urls
        assert field_name in field_names


def analyze_field_names(field_names):
    """
    Desc: a function that decides what fields are has_many and what are single_value
        aka what will be a list of values versus single value
    Args:
        field_names (list): all the field names from the original metadata information provided
    Returns: touple of where first value is the names of items which will be single values.
        second item of touple is the names of fields which will be lists and are \
        currently labeled like creator1 creator2 creator3

    """
    repeating_field_names = set()
    singular_field_names = set()
    for field_name in sorted(field_names):
        match = re.fullmatch('(.+)(\d+$)', field_name)
        if not match:
            singular_field_names.add(field_name)
        else:
            name_part, number_part = match.groups()
            while re.match('\d',name_part[-1]):
                number_part = name_part[-1] + number_part
                name_part = name_part[:-1]
            if number_part == '1':
                repeating_field_names.add(name_part)
            elif name_part not in repeating_field_names:
                singular_field_names.add(field_name)
    if 'files' in singular_field_names:
        singular_field_names.remove('files')
    if 'fulltext_url' in singular_field_names:
        singular_field_names.remove('fulltext_url')
    if 'first_file' in singular_field_names:
        singular_field_names.remove('first_file')
    log.debug('Singular field names: {}'.format(singular_field_names))
    log.debug('Repeating field names: {}'.format(repeating_field_names))
    return singular_field_names, repeating_field_names


def create_repository_metadata(row, singular_field_names, repeating_field_names):
    """
    DESC: given a line from the csv this function returns a dictionary of metadata
         with lists instead of repeated fileds followed by a number
         ie { "title": "joe","creator1": "larry", "creator2" : "james" }
         becomes { "title": "joe","creator": ["larry", "james"] }
    Args:
        row (dict): a line from the csv with fieldname:value (as a dict)
        singular_field_names (set): a list of fields that are not to be listsself.
            calculated in analyze_field_names()
        repeating_field_names (set): a list of field names which will be lists (has many) not single value
    Return: dict representing metadata
    """
    metadata = dict()
    for field_name in singular_field_names:
        metadata[field_name] = row[field_name] if row[field_name] != '' else None
    for field_name in repeating_field_names:
        metadata[field_name] = list()
        field_incr = 1
        while True:
            field_name_incr = '{}{}'.format(field_name, field_incr)
            if field_name_incr in row:
                if row[field_name_incr] != '':
                    metadata[field_name].append(row[field_name_incr])
            else:
                break
            field_incr += 1

    return metadata


def find_files(row_filepath, row_first_filepath, base_filepath):
    """
    Desc: this function will locate all the files and check to ensure the primary file is present
    Args: row_filepath (str) the path to the file or directory that contains relevent resourcesself.
    Return: touple
        first element (str): path to the primary file
        second element (set): list of other files relating to the work (does not include primary file)
    """
    filepath = os.path.join(base_filepath, row_filepath)
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)
    files = set()
    if os.path.isfile(filepath):
        files.add(filepath)
    else:
        for path, _, filenames in os.walk(filepath):
            for filename in filenames:
                files.add(os.path.join(path, filename))
    # Make sure at least one file
    if not files:
        raise FileNotFoundError('Files in {}'.format(filepath))
    # Either a row_first_filepath or only one file
    if not (row_first_filepath or len(files) == 1):
        raise FileNotFoundError('First file')
    if row_first_filepath:
        first_file = os.path.join(base_filepath, row_first_filepath)
        if not os.path.exists(first_file):
            raise FileNotFoundError(first_file)
        if not first_file in files:
            raise FileNotFoundError('{} not in files'.format(first_file))
    else:
        first_file = list(files)[0]
    files.remove(first_file)
    return first_file, files


def repo_import(repo_metadata_filepath, title, first_file, other_files, repository_id, ingest_command,
                ingest_path, ingest_depositor):
    """
    Desc: this function takes in relevant information and paths and calls the rake
        task to ingest the work into Hyrax
    Args:
        repo_metadata_filepath (str): path to the file which contains nested json
            representing the metadata (basically the python dict in a file)
        title (str): the title of the work to be uploaded
        first_file (str): the path to the primary file
        other_files (set): list of the rest of the file paths
        repository_id (str or None): [Optional] id of the original work to which
            this is an update if None this is a new work to add
        ingest_command (str): the command to execute the rake task - set in the
            config.py file
        ingest_path (str): the directory of our rails project - set in config.py
        ingest_depositor (str): the username of the person depositing the
            information - set in the config.py file
    Returns: the id of the work in hyrax
    """
    log.info('Importing %s.', title)
    # rake gwss:ingest_etd -- --manifest='path-to-manifest-json-file' --primaryfile='path-to-primary-attachment-file/myfile.pdf' --otherfiles='path-to-all-other-attachments-folder'
    command = ingest_command.split(' ') + ['--',
                                           '--manifest=%s' % repo_metadata_filepath,
                                           '--primaryfile=%s' % first_file,
                                           '--depositor=%s' % ingest_depositor]
    if other_files:
        command.extend(['--otherfiles=%s' % ','.join(other_files)])
    if repository_id:
        log.info('%s is an update.', title)
        command.extend(['--update-item-id=%s' % repository_id])
    log.info("Command is: %s" % ' '.join(command))
    output = subprocess.check_output(command, cwd=ingest_path)
    repository_id = output.decode('utf-8').rstrip('\n')
    log.info('Repository id for %s is %s', title, repository_id)
    return repository_id


if __name__ == '__main__':
    import config

    parser = argparse.ArgumentParser(description='Loads into GW Scholarspace from CSV')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('csv', help='filepath of CSV file')
    parser.add_argument('--url', action='store_true')
    args = parser.parse_args()
    run_ingest_process(args.csv,config.ingest_command, config.ingest_path, config.ingest_depositor,url = args.url,debug = args.debug)
