# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yixuan Zhao <johnsonqrr (at) gmail.com>

# DATA: http://gitlab.polomi.com/polomi/projectmanage/tree/master
"""
Usage: datastore_loader.py  DATA_DIR RESOURCE_ID PRIMAY_KEYS...

Options:
-h --help                 Show this screen.
-v --version              Show version


"""
import os
import sys
import requests
import json
import hashlib
import re
import pandas as pd

from docopt import docopt
from unidecode import unidecode
from urlparse import urljoin
from lib.munge import munge_title_to_name
from collections import OrderedDict
from config import HOST, API_KEY, ROOT_PACKAGE_ID


# API doc：http://docs.ckan.org/en/latest/maintaining/datastore.html
def clean_header(headers):
    cleaned_headers = []
    for header in headers:
        if header.startswith('_'):
            header = re.sub('^_*', '', header)
        cleaned_headers.append(header)
    return clean_header

def read_csv_data(file_path):
    # NOTE:数据文件中有诸如_template、_cached_page_id的header，是爬虫自身相关的信息，不能被datastore合法储存，合适的做法是将其抛弃。
    # 对应的datapusher的做法是删除下划线后保存为新的列。
    # 但如此一来就造成了两套系统相反的处理方式，且需要编辑遵守相应命名规则，为方便起见先将这些“无效数据”上传上去。
    with open(file_path) as f:
        data_df = pd.read_csv(f)

    data_df.rename(columns=lambda header: re.sub('^_*', '', header), inplace=True)
    data_df = data_df.where(pd.notnull(data_df), None)
    headers = list(data_df.columns)  #  TODO: 保留header顺序 
    records = data_df.to_dict('records')

    return records, headers

def read_json_data(file_path):
    records = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line:
                record = json.loads(line)
                for k, v in record.iteritems():
                    if isinstance(v, list):     # "货币":["泰国铢"]
                        record[k] = v[0]
                records.append(record)

    # 这里用pandas略显多余，只是为了较方便地clean header，就与csv格式的统一起来了
    # 未来可以考虑引入datapusher的clean方法
    data_df = pd.read_json(json.dumps(records), orient='records')
    data_df.rename(columns=lambda header: re.sub('^_*', '', header), inplace=True)
    headers = list(data_df.columns)  #  TODO: 保留header顺序 
    records = data_df.to_dict('records')

    return records, headers

def check_resource_exist(resource_id):
    r = requests.get(
        urljoin(HOST,'api/action/datastore_search?resource_id={}'.format(resource_id)),
        headers={
            'Authorization': API_KEY,
            'Content-Type' : 'utf-8',
        }
    )
    return json.loads(r.content)['success']

def create_resource_primaykey(records, resource_id, primary_key):
    r = requests.post(
        urljoin(HOST, 'api/action/datastore_create'),
        data = json.dumps({
                'resource_id'   : resource_id,
                'force'         : True,
                'records'       : records,
                'primary_key'   : primary_key,
        }),
        headers={
            'Authorization': API_KEY,
            'Content-Type' : 'utf-8',
        }
    )
    try:
        return json.loads(r.content)[u'success']
    except:
        return False

def upsert_resource(records, resource_id, primary_key):
    r = requests.post(
        urljoin(HOST, 'api/action/datastore_upsert'),
        # urljoin(HOST, 'api/action/datastore_delete'),
        data = json.dumps({
                'resource_id'   : resource_id,
                'force'         : True,
                'records'       : records,
                'method'        :'upsert',
        }),
        headers={
            'Authorization': API_KEY,
            'Content-Type' : 'utf-8',
        }
    )
    try:
        item = json.loads(r.content)
        return item['success']
    except:
        return False

def send_records_to_datastore(records, resource_id, primary_key):
    exist = check_resource_exist(resource_id)
    if exist:
        print 'Upserting.....'
        return upsert_resource(records, resource_id, primary_key)
    else:
        print 'Switch to datastore_create ...'
        return create_resource_primaykey(records, resource_id, primary_key)

def main():
    # TODO:增加delete option
    # python datastore_loader.py  '/Users/johnson/projectmanage/scrapinghub-test/downloaded data' 45d9dfe4-9792-4304-a6b0-8d9b898b479f 发布时间 货币名称
    arguments = docopt(__doc__, version='Ckan Datastore Uploader 1.0')
    print arguments
    data_dir = arguments['DATA_DIR']
    PRIMAY_KEYS = arguments['PRIMAY_KEYS']
    resource_id = arguments['RESOURCE_ID']
    files = os.listdir(data_dir)

    for filename in files:
        if not (filename.endswith('.csv') or filename.endswith('.json')):
            print 'ignore the file : {}'.format(filename)
            continue

        print 'dealing with {}...'.format(filename)
        file_abs_path = os.path.join(data_dir, filename)
        if filename.endswith('.csv'):
            records, headers = read_csv_data(file_abs_path)
        elif filename.endswith('.json'):
            records, headers = read_json_data(file_abs_path)
        success = send_records_to_datastore(records, resource_id, PRIMAY_KEYS)

        if success:
            print 'succeed'
        else:
            print 'failed'


if __name__ == '__main__':
    # 认为是针对具体resource的更新，文件扁平化储存。
    # upload_datastore.py {file_name} {resource_id} {primary_keys}
    main()