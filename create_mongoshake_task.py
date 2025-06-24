#-*- coding: UTF-8 -*-
import requests

url = "http://localhost:5000/create_task"
####################################
###  mongoshake2.4.6  支持3.6->4.2
###  mongoshake2.8.4 支持4.2->6.0
####################################


data = {
    "source_addr": "mongodb://admin:xxxxxx@10.10.10.1:27017",
    "target_addr": "mongodb://admin:xxxxxx@10.20.18.1:27017",
    "business_info": "my_important_data",
    "sync_mode": "all",  # 可选: all, full, incr
    "filter_namespace_white": "mcd"   # ;分割
}

response = requests.post(url, json=data)
print(response.json())

