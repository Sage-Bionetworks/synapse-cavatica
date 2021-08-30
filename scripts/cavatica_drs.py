"""Interact with DRS API on cavatica"""
import os
import requests
import urllib.parse

import sevenbridges as sbg


DRS_HOST = "https://cavatica-ga4gh-api.sbgenomics.com"


def get_drs_object(object_id, sbg_auth):
    """Get DRS object from CAVATICA DRS server"""
    endpoint = f'ga4gh/drs/v1/objects/{object_id}'
    drs_api = urllib.parse.urljoin(DRS_HOST, endpoint)
    response = requests.get(drs_api, headers={"X-SBG-Auth-Token": sbg_auth})
    return response


def get_drs_object_url(object_id, sbg_auth, access_id="aws-us-east-1"):
    """Get URL to download file from CAVATICA DRS server"""
    endpoint = f'ga4gh/drs/v1/objects/{object_id}/access/{access_id}'
    drs_api = urllib.parse.urljoin(DRS_HOST, endpoint)
    response = requests.get(drs_api, headers={"X-SBG-Auth-Token": sbg_auth})
    return response


def drs_download(object_id, sbg_auth, download_location="./"):
    """Downloads file from CAVATICA DRS server"""
    resp = get_drs_object(object_id=object_id, sbg_auth=sbg_auth)
    resp_json = resp.json()

    dl_url_resp = get_drs_object_url(
        object_id=object_id, sbg_auth=sbg_auth,
        access_id=resp_json['access_methods'][0]['access_id']
    )
    dl_url_resp_json = dl_url_resp.json()

    dl_file = requests.get(dl_url_resp_json['url'], allow_redirects=True)
    file_path = os.path.join(download_location, resp_json['name'])
    with open(file_path, "wb") as dl_f:
        dl_f.write(dl_file.content)
    return file_path


def main():
    """download file via CAVATICA DRS server"""
    # Set up cavatica sbg config profile
    config_file = sbg.Config(profile='cavatica')
    # tsv file
    object_id = "60c8e1c3eba762583a79cd18"
    tsv_test_path = drs_download(
        object_id=object_id,
        sbg_auth=config_file.auth_token
    )
    # gz file
    gz_file = drs_download(
        object_id="60c8e134eba762583a79cc25",
        sbg_auth=config_file.auth_token
    )
