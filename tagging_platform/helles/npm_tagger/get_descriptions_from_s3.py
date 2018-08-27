"""Collects the package descriptions from S3 and dumps output into the JSON file.

This script collects the description(s) for a tagged package from S3 core-data bucket,
and dumps the aggregated output into the input bucket from where the package tag map
was read.
"""

from util.data_store.s3_data_store import S3DataStore
from analytics_platform.kronos.src import config
import os
import daiquiri
import logging

daiquiri.setup(level=logging.WARN)
logger = daiquiri.getLogger(__name__)


def run(ecosystem='npm', bucket_name='prod-bayesian-core-data',
        input_data_path=''):
    """Collect the package descriptions from S3 and dump output into the JSON file."""
    if not input_data_path:
        logger.warning("No data path given, not proceeding further.")
        return
    core_data = S3DataStore(src_bucket_name=bucket_name,
                            access_key=config.AWS_S3_ACCESS_KEY_ID,
                            secret_key=config.AWS_S3_SECRET_ACCESS_KEY)
    input_bucket_name, key = input_data_path.split('/', 2)[-1].split('/', 1)
    input_bucket = S3DataStore(src_bucket_name=input_bucket_name,
                               access_key=config.AWS_S3_ACCESS_KEY_ID,
                               secret_key=config.AWS_S3_SECRET_ACCESS_KEY)

    package_tag_map = input_bucket.read_json_file(key)
    package_list = list(package_tag_map.keys())
    descriptions = {}

    for package in package_list:
        print("Running for: {}".format(package))
        version_folders = sorted(core_data.list_folders(
            prefix=os.path.join(ecosystem, package)), reverse=True)
        if not version_folders:
            logger.warning("No data exists for {}".format(package))
            continue
        latest_version = version_folders[0]
        try:
            meta = core_data.read_json_file(
                os.path.join(latest_version, 'metadata.json'))
        except Exception:
            logger.warning(
                'No metadata exists in S3 for the package: {}'.format(package))
            continue
        if 'details' in meta and len(meta['details']) > 0:
            descriptions[package] = meta['details'][0].get(
                'description', '')
        else:
            descriptions[package] = ''
    input_bucket.write_json_file(
        'tagging/npm/package_descriptions.json', descriptions)
