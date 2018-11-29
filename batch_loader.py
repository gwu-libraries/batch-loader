import argparse
import logging
import csv
import re
import tempfile
import json
import os
import shutil
import subprocess

log = logging.getLogger(__name__)

required_field_names = (
    'files',
    'resource_type1',
    'title1',
    'creator1',
    'license1',
    'rights_statement'
)


def load_csv(filepath):
    """
    Reads CSV and returns field names, rows
    """
    log.debug('Loading csv')
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile)
        return reader.fieldnames, list(reader)


def validate_field_names(field_names):
    log.debug('Validating field names')
    for field_name in required_field_names:
        assert field_name in field_names


def analyze_field_names(field_names):
    repeating_field_names = set()
    singular_field_names = set()
    for field_name in sorted(field_names):
        match = re.fullmatch('(.+)(\d+)', field_name)
        if not match:
            singular_field_names.add(field_name)
        else:
            name_part, number_part = match.groups()
            if number_part == '1':
                repeating_field_names.add(name_part)
            elif name_part not in repeating_field_names:
                singular_field_names.add(field_name)
    singular_field_names.remove('files')
    singular_field_names.remove('object_id')
    singular_field_names.remove('depositor')
    if 'first_file' in singular_field_names:
        singular_field_names.remove('first_file')
    log.debug('Singular field names: {}'.format(singular_field_names))
    log.debug('Repeating field names: {}'.format(repeating_field_names))
    return singular_field_names, repeating_field_names


def create_repository_metadata(row, singular_field_names, repeating_field_names):
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
    if row_filepath is '':
        # We will interpret this as "No files to load or update"
        print("row_filepath is None")
        return None, None

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
    log.info('Importing %s.', title)
    # rake gwss:ingest_etd -- --manifest='path-to-manifest-json-file' --primaryfile='path-to-primary-attachment-file/myfile.pdf' --otherfiles='path-to-all-other-attachments-folder'
    command = ingest_command.split(' ') + ['--',
                                           '--manifest=%s' % repo_metadata_filepath,
                                           '--depositor=%s' % ingest_depositor]
    if first_file:
        command.extend(['--primaryfile=%s' % first_file])
    if other_files:
        command.extend(['--otherfiles=%s' % ','.join(other_files)])
    if repository_id:
        log.info('%s is an update.', title)
        command.extend(['--update-item-id=%s' % repository_id])
        if first_file is None:
            command.extend(['--skip-file-updates'])
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

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO
    )
    logging.basicConfig(level=logging.DEBUG)

    field_names, rows = load_csv(args.csv)
    log.info('Loading {} object from {}'.format(len(rows), args.csv))
    validate_field_names(field_names)
    singular_field_names, repeating_field_names = analyze_field_names(field_names)

    base_filepath = os.path.dirname(os.path.abspath(args.csv))

    for row in rows:
        metadata = create_repository_metadata(row, singular_field_names, repeating_field_names)
        metadata_temp_path = tempfile.mkdtemp()
        metadata_filepath = os.path.join(metadata_temp_path, 'metadata.json')
        try:
            with open(metadata_filepath, 'w') as repo_metadata_file:
                json.dump(metadata, repo_metadata_file, indent=4)
                log.debug('Writing to {}: {}'.format(metadata_filepath, json.dumps(metadata)))
            try:
                first_file, other_files = find_files(row['files'], row.get('first_file'), base_filepath)
                depositor = row['depositor']
                update_object_id = row['object_id']
                repo_id = repo_import(metadata_filepath, metadata['title'], first_file, other_files,
                                      update_object_id,
                                      config.ingest_command,
                                      config.ingest_path,
                                      depositor)
                # TODO: Write repo id to output CSV
            except Exception as e:
                # TODO: Record exception to output CSV
                raise e
        finally:
            if (not config.debug_mode) and os.path.exists(metadata_filepath):
                shutil.rmtree(metadata_temp_path, ignore_errors=True)
