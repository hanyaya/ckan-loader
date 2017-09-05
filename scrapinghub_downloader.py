# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yixuan Zhao <johnsonqrr (at) gmail.com>

# get the scrapyed data via scrapyinghub API

"""
Usage: scrapinghub_downloader.py [options] <project_id> <job_unit> <output_dir>

Options:
-h --help                 Show this screen.
-v --version              Show version
-s ID, --start <ID>       The start job id[default: 0]
-e ID, --end <ID>         The end job id

#example : python scrapinghub_downloader.py --start 180 --end 200  216887 1 /path/to/your/data

"""

from docopt import docopt
import os

API_key = '67195753cf284b5b99720f71e24f9155'
FILE_PREFIX = 'items_www.boc.cn'

def main():
    # TODO:未来数据量如进一步扩大，可以增加一些检测机制以节约时间，避免重复访问浪费时间
    arguments = docopt(__doc__, version='scraping hub downloader 1.0')
    print arguments
    command_format = 'curl -u {api_key}: https://storage.scrapinghub.com/items/{project_id}/{job_unit}/{job_id} -o {output_file}'
    start = int(arguments['--start'])
    end   = int(arguments['--end'])
    project_id = arguments['<project_id>']
    output_dir = arguments['<output_dir>']
    job_unit = arguments['<job_unit>']
    for job_id in range(start, end + 1):
        output_file_abspath = os.path.join(output_dir, '{}_{}.json'.format(FILE_PREFIX, job_id))
        command = command_format.format(
                                    api_key=API_key,
                                    project_id=project_id,
                                    job_unit=job_unit,
                                    job_id=job_id,
                                    output_file=output_file_abspath)
        print 'downloading the job: {}'.format(job_id)
        os.system(command)

if __name__ == '__main__':
    main()