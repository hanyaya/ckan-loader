### loader.py使用说明（依赖config.py）
#### 更改配置文件`config.py`
1. 设置HOST地址，即所要上传的ckan网址（如http://ckan-int.polomi.com/）
2. 更改api-key为具有管理权限的账户对应api-key
3. 设置data-dir，是储存数据文件夹的绝对路径
4. 设置ROOT_PACKAGE_ID，必须是一个已经存在的dataset，概念上是ckan数据的最顶层。

#### 安装依赖库
`pip install -r requirements.txt` 
此文件使用pipreqs生成，pandas包的初次安装较为繁琐。 

#### 添加metadata
如果只增加一批数据如“中国人口”，metadata应位于 data/中国人口/.metadata.json 
每批数据至少需要一个metadata，以指定添加到哪个organization。  
如需要对某个dataset（文件夹）定制相应的描述等，则需在此文件夹下再添加一个`.metadata.json`

#### 运行
`python loader.py [your_batch_id]`  
此处的`batch_id`作为一个标识，是数据集slug的前缀，如果不填则默认为polomi。

### 说明
本repo是一个从爬虫端（更确切地说是DC端）上传数据到ckan端的范例。
### 基本假设
目前假设数据主要以csv、xls、json格式储存。（参考http://gitlab.polomi.com/polomi/projectmanage/issues/21 中的调研）。  
### 数据导入
* 文件夹的命名即代表dataset的title，允许带空格、中文、特殊字符等，命名不需要规范。
* 类似地，文件的命名代表resource的title。

### 增量更新的问题
DC处采取何种增量爬取方式？ 
1. 在一个老文件后面增加一个新文件。两者互补并不重叠 or 两者互补且有重叠  
2. 直接将老文件替换为新文件，新文件是增量爬取的数据
3. 对uploader最简单的是，在老文件的底部写入新文件，这类情况做一下去重操作即可重新上传。`resource_update`允许直接从文件更新数据。

DP对于增量更新，只更新datastore吗，filestore仍然是老数据？
（可能依赖primary key的相关设置与调用）  

### metadata 
#### metadata的格式（YML or JSON ？）
metadata字段介绍，带*号是必要字段。
（因为metadata原生字段和前端几乎差不多，只有首字母大写和少数一两个字段的叫法不同，这里就直接用model里本身的字段来表示）
未来如果要翻译成和前端一模一样的字段，需要加一个映射处理过程。    
```
owner_org: human-rights
private: true                  // 对应前端的'Visibility'，如果是public此处选择false
author: "zhaoyixuan"
author_email: zhaoyixuan@polomi.com
notes: 在这里填写description，支持markdown语法与转义缩进
license_id: notspecified / odc-odbl / odc-by...  // 参照http://ckan-int.polomi.com/api/3/action/license_list ,允许自定义
maintainer: zhaoyixuan
maintainer_email: zhaoyixuan@polomi.com
version: 1.0beta
url: "http://data.nanhai.gov.cn/" // 这个'url'就是前端网页的'source'字段，代表数据来源
tags: 
  - name: 
      this is tag1
  - name: 
      这是标签2
  - name: 
      还有更多的标签依此类推
  - name:
      不要标签的话删掉整个tags
extras:         # extras是自定义字段，可以随意增加field。对应前端的'Custom Field'
  - value:
      使用权限
    key:
      无
  - value:
      resource download url
    key: ""
  - value:
      数据使用案例
    key:
      无
其他基本和前端一致
```
* 关于字段类型，除了private，其它全是字符型。
* 不同于前端会进行的各种检查，一些不规范操作诸如在metadata.json里email不带@、license_id 随便填写'12345'等也是被允许的。可以说从ckan方面来说几乎不会面临越界问题。

#### metadata的沿用
如果一个dataset的metadata为空，则向上回溯，沿用离其最近的祖先的metadata。  
考虑到metadata中的description需要频繁更新，编辑为了给每一层加不同的desc，就需要多次复制黏贴，更改desc字段。 如有需求可以做相关开发将其分离出来。  
一些构想：patch和update两种更新模式。
### 关于软连接
可以认为是windows里的快捷方式或MAC里的替身,软连接是合法的，也会建立相关relationship。 
#### 文件树状结构图
```
$ tree -N
.
├── human rights
│   ├── Economic Freedom and Press Freedom
│   │   └── economic-freedom.csv
│   ├── Fragile States Index – Human Rights Dimension
│   │   └── human-rights-violations.csv
│   ├── Protection from political repression and violations of “physical integrity rights”
│   │   └── human-rights-protection.csv
│   ├── Treatment of Other Races in the USA Post-1950
│   │   ├── Interracial Marriages
│   │   │   └── US-Map-of-Dates-of-Repeal-of-US-Anti-Miscegenation-Laws-by-State-Wikipedia0.png
│   │   ├── Number of Interracial Marriages
│   │   │   └── Share-married-to-someone-from-a-different-raceethnicity-1980-2008-Pew0.png
│   │   ├── Opinions on Interracial Marriage
│   │   │   └── approve-or-disapprove-of-marriage-between-blacks-and-whites.png
│   │   └── Racism outside the USA
│   │       ├── Discriminatory and affirmative action policies
│   │       │   └── Trends-in-Political-Discrimination-1950-2003-Marshall-and-Gurr-2005.png
│   │       └── Students’ attitudes towards equal rights for ethnic minorities by level of civic knowledge
│   │           └── students-attitudes-towards-equal-xxx.png
│   └── metadata.yml
├── 各类文件示例
│   ├── metadata.yml
│   ├── png文件示例.png
│   ├── testyml.py
│   ├── who-aap-database-may2016.xlsx
│   ├── zip文件示例.zip
│   └── 这是一个PDF.pdf
└── 科技数据统计
    ├── metadata.yml
    ├── 产品质量监督检查情况
    │   ├── 产品质量监督检验企业数
    │   │   └── 产品质量监督检验企业数.csv
    │   ├── 产品质量监督检查批次合格率
    │   │   └── 产品质量监督检查批次合格率.csv
    │   └── 产品质量监督检查有不合格产品企业所占比例
    │       └── 产品质量监督检查有不合格产品企业所占比例.csv
    ├── 诺贝尔数学奖获得情况
    ├── 国内外三种专利申请受理量
    │   ├── 发明专利申请受理量.csv
    │   ├── 诺贝尔数学奖获得情况 -> /Users/johnson/ckan-data-loader/data/科技数据统计/诺贝尔数学奖获得情况
    │   ├── 外观设计专利申请受理量.csv
    │   └── 国内实用新型专利申请受理量.csv
    └── 在这一层也允许创建数据但是不提倡.csv



```
### 文件结构说明
1. 原则上一个母文件夹下要么全是file，要么全是文件夹，不建议两者混合:如示例中的“科技数据统计”下的"在这一层也允许创建数据但是不提倡.csv"。这种情况会导致"不提倡.csv"被加入到“科技数据统计”这个原本为空的数据集下，可能会导致一些困惑。
2. "诺贝尔数学奖获得情况" 是一个空目录的示例，即使其下面无任何数据也是合法的。
3. "国内外三种专利申请受理量"是一个“一对多”目录的示例，一个dataset(package)下对应三个resource，即三张表。
4. "产品质量监督检查情况"的子目录是“1对1”示例，出于某种原因，每个dataset都对应一个同名的csv文件。显然这些层次是可以模仿3中结构“向上缩一层”的。此类储存结构也是合法的。
5. 另一个human rights的文件夹从 https://ourworldindata.org/human-rights 处取部分样品数据，其中包括csv和png图片，还原真实情况。较长的带空格的文件夹名字也是被允许的。

### datastore_loader.py 使用说明（依赖config.py）
`python datastore_loader.py  [dir_path] [resource_id] [primary_keys...]`   
如：  
`python datastore_loader.py  '/path/to/your/data' 45d9dfe4-9792-4304-a6b0-8d9b898b479f 发布时间 货币名称`  
可以读取`/path/to/your/data` 中的所有文件，进行上传。HOST与相应的apikey也是在config.py中指定。

### scrapinghub_downloader.py使用说明（不依赖config.py）
`python scrapinghub_downloader.py --start [start_id] --end [end_id]  [project_id] [job_unit] /path/to/your/data`   
如：  
`python scrapinghub_downloader.py --start 180 --end 200  216887 1 /path/to/your/data`  

配合网页 https://app.scrapinghub.com/p/216887/jobs 进行参数说明：   
可以看到Completed Jobs 列表里有很多job，每个job的编号形如1/194、1/193。  
1就是job_unit,193、194就是job_id。因此在运行时要指定起始与终止 ID，脚本会下载这两个ID之间的所有数据。（允许与本地旧数据重叠，新的数据会覆盖旧数据）。  
project就是网址里的`216887`这个数字。 
最后的路径是储存数据目录的路径。  

与 datastore_loader.py配合使用时：
1. 先用downloaer下载数据到data文件中。
2. 下载完后运行datastore_loader.py，指定与1中相同的文件夹，上传。