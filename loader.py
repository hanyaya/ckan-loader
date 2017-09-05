# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yixuan Zhao <johnsonqrr (at) gmail.com>
import os    
import sys
import requests
import json
import hashlib
import yaml

from unidecode import unidecode
from urlparse import urljoin
from lib.munge import munge_title_to_name, munge_filename
from config import HOST, API_KEY, DATA_DIR, ROOT_PACKAGE_ID, DEFAULT_PREFIX

def slugify_with_prefix_suffix(directory, title):
    #prefix由编辑自定义，不hash，suffix是文件路径的签名切片
    abs_path_of_tree = directory.replace(DATA_DIR, '')

    if not isinstance(title, unicode):
        title = title.decode('utf-8')
    title_slug = munge_title_to_name(title)[:80]
    prefix = PREFIX
    sig_of_path = hashlib.sha256(abs_path_of_tree).hexdigest()

    slug ='{prefix}_{title_slug}_{suffix}'.format(
            prefix=prefix,
            title_slug=title_slug,
            suffix=sig_of_path[:6]
        )
    return slug
    # polomi_guo-nei-wai-san-chong-zhuan-li-shen-qing-shou-li-liang_35f95b

def create_single_resource(package_slug, file_path):
    # 上传multipart/form-data时headers不能指定content type，必须要让requests接受到files参数后自动生成方可
    resource_name = os.path.split(file_path)[-1]
    if not isinstance(resource_name, unicode):
        resource_name = resource_name.decode('utf-8')
    resource_slug = munge_filename(resource_name)
    multiform_data = {
        'upload' :   (resource_slug, open(file_path, 'rb')),
        "package_id":('', package_slug),
        "name"      :('', resource_name)
    }
    r =requests.post(
        urljoin(HOST, '/api/action/resource_create'),
        headers={'Authorization': API_KEY},
        files=multiform_data
    )
    try:
        item = json.loads(r.content)  
        print item
        return item['success']
    except:
        return False

def update_single_resource(package_slug, file_path):
    pass

def check_resource_exist(package_slug, file_path):
    pass

def upload_single_resource(resource):
    pass

def create_all_resources(resources):
    # TODO:查重，原则上我们认为名称相同的resource是同一个文件（即使ckan允许重名）
    # A.最朴素的方法是检验同名resource是否存在: 选择 update or create， 如果存在多个，还要进行delete。
    # B.也可以选择在更新package时直接切到“update”模式，则会删除掉其中的所有resource，然后在create_all_resources时进行全面重新添加。
    # 第二种方法更简便，但是要求每次运行脚本时，DATA文件中总是保持全量数据，否则会出现数据缺失。

    success = fail = 0
    fail_list = []
    for resource in resources:
        file_path = resource['file_path']
        package_slug = resource['package_slug']
        if create_single_resource(package_slug, file_path):
            print 'upload file success'
            success += 1
        else:
            fail_list.append(file_path)
            fail += 1
    print 'creating resources succeed: {}\t failed:{}'.format(success, fail)
    if fail > 0:
        print 'The failed ones are:'
        print '\n'.join(fail_list)


def create_single_relationship(data):
    # relationship更新起来会比较麻烦，需要删除原来的再添加新的。
    # 直接create的话完全无视原来逻辑，例如会导致A既是B的child，同时又是B的parent这种情况产生
    r = requests.post(
        urljoin(HOST,'/api/action/package_relationship_create'),
        data=json.dumps(data),
        headers={'Authorization': API_KEY, 'content-type':'application/json;charset=utf-8'}
    )
    # print r.content

    try:
        item = json.loads(r.content)  
        return item['success']
    except:
        # print r.content
        print data['subject'], data['object']
        return False

def create_all_relationships(relationships):
    success = fail = 0
    fail_list = []
    for relationship in relationships:
        parent_slug = relationship['parent_slug']
        child_slug  = relationship['child_slug']
        data = {
            'subject':parent_slug,
            'object':child_slug,
            'type':'parent_of',
        }
        if create_single_relationship(data):
            success += 1
        else:
            fail  += 1
            fail_list.append(relationship)
    print 'creating relationships succeed: {}\t failed:{}'.format(success, fail)
    if fail > 0:
        print 'The failed ones are:'
        for rel in fail_list:
            print rel

def update_single_package(data):
    # 不能使用package_update,那样会删除原来的resource。（如果想一次重新全量导入，需使用update）
    # TODO:目前的patch模式如果重复运行脚本，则会重复添加resource，设置一个切换成update的模式？
    r = requests.post(
        # urljoin(HOST, 'api/action/package_patch'),
        urljoin(HOST, 'api/action/package_update'),
        data=json.dumps(data),
        headers={'Authorization': API_KEY, 'content-type':'application/json;charset=utf-8'}
    )
    try:
        if json.loads(r.content)['success']:
            print 'updating package succeed!'
            return True
    except:
        return False


def create_single_package(data):
    r = requests.post(
        urljoin(HOST, 'api/action/package_create'),
        data=json.dumps(data),
        headers={'Authorization': API_KEY, 'content-type':'application/json;charset=utf-8'}
    )
    try:
        item = json.loads(r.content)
        if item['success']:
            print 'creating package succeed!'
            return True
        elif item['error']['name'] == ['That URL is already in use.']:
            print ('The package "{}" already exists, we\'ll update it.'.format(data['title']))
            data['id'] = data['name']
            return update_single_package(data)
    except Exception, e:
        print r.content
        return False


def create_all_packages(packages):
    # 进入下一个函数前，在这一层就要确定slug了。
    success = fail = 0
    fail_list = []
    for package in packages:
        package_title = package['title']
        slug = package['slug']
        data = {   
                'name': slug,
                'private':True,
                'title':package_title,
        }
        data.update(package['metadata'])
        if create_single_package(data):
            success += 1
        else:
            fail  += 1
            fail_list.append(package_title)
    print 'creating packages succeed: {}\tfailed:{}'.format(success, fail)
    if fail > 0:
        print 'The failed ones are:'
        print '\n'.join(fail_list)

def dfs(directory, metadata=None):
    # depth first search
    packages, relationships, resources = [], [], []
    # 涉及递归，谨慎处理。尤其是软连接
    # print directory
    names_list = os.listdir(directory)
    if 'metadata.yml' in names_list: # or yml?
        meta_file = os.path.join(directory, 'metadata.yml')
        # print meta_file
        with open(meta_file, 'r') as f:
            metadata = yaml.load(f)

    parent_title = os.path.split(directory)[1]
    parent_slug = slugify_with_prefix_suffix(directory, parent_title)
    packages.append({'title': os.path.split(directory)[1], 
        'metadata':metadata, 
        'slug':parent_slug})

    for name in names_list:
        sub_path = os.path.join(directory, name)
        if name.startswith('.') or name=='metadata.yml':
            continue
        elif not os.path.isdir(sub_path):           # 是文件，上传
            package_title = os.path.split(directory)[1]
            resources.append({'package_slug':parent_slug, 'file_path':sub_path})
        else : 
            # 是子文件夹，则添加package的同时建立父子关系,metadata都是引用，不必担心开销过大。
            child_title = os.path.split(sub_path)[1]
            child_slug = slugify_with_prefix_suffix(sub_path, child_title)

            if not os.path.islink(sub_path):          # 防止进入环（实测即使成环也只循环几十圈就停止，不会无限下去）
                relationships.append({'parent_slug':parent_slug, 'child_slug':child_slug})
                abs_path = os.path.join(directory, child_title)
                new_packages, new_relationships, new_resources = dfs(sub_path, metadata)
                if new_packages:
                    packages.extend(new_packages)
                if new_relationships:
                    relationships.extend(new_relationships)
                if new_resources:
                    resources.extend(new_resources)
            else:   # 如果成环，则读出其真实路径后建立关系
                child_slug = slugify_with_prefix_suffix(os.readlink(sub_path), child_title)
                relationships.append({'parent_slug':parent_slug, 'child_slug':child_slug})


    return packages, relationships, resources

def main():
    top_datasets = os.listdir(DATA_DIR)
    for top_dataset in top_datasets:
        if not os.path.isdir(os.path.join(DATA_DIR, top_dataset)):
            continue
        metadata_path = os.path.join(DATA_DIR, top_dataset, 'metadata.yml')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = yaml.load(f)
        else:
            print ('We need a metadata file in {}!!'.format(top_dataset))
            continue
        # 还有一种传参方法是将这3个都传到dfs里，不return，可以省略很多内部代码，但是参数表会显得过于冗长。
        packages, relationships, resources = dfs(os.path.join(DATA_DIR, top_dataset), metadata)

        root_slug = ROOT_PACKAGE_ID

        # abs_path 不是系统的abs_path,而是从DATA根节点出发的路径
        # top_dataset_slug = slugify_with_prefix_suffix(os.path.join(DATA_DIR, top_dataset), top_dataset)
        # packages.append({'title':top_dataset, 'metadata':metadata,'slug':top_dataset_slug})
        # relationships.append({'parent_slug':root_slug, 'child_slug':top_dataset_slug})

        create_all_packages(packages)
        create_all_resources(resources)
        create_all_relationships(relationships)
        # TODO？:增加command line 选项，可以只执行其中的一两步
        # print relationships

        # resource 的 metadata只有一个field,“description”先不考虑

if __name__ == '__main__':
    if len(sys.argv) > 1:
        PREFIX = sys.argv[1]
    else:
        PREFIX = DEFAULT_PREFIX
    print 'using prefix as: {}'.format(PREFIX)
    main()