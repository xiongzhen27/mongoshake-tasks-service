#### mongoshake-tasks-manager

快速使用
-------
- 服务端
```shell
nohup  python Mongo_Shake_Task_Run.py &
```
- 客户端
Linux/macOS (bash):

```shell
curl -X POST http://localhost:5000/create_task \
-H "Content-Type: application/json" \
-d '{
    "shake_version": "2.4.6",
    "source_addr": "mongodb://admin:xxxxxx@10.10.10.1:27017",
    "target_addr": "mongodb://admin:xxxxxx@10.20.18.1:27017",
    "business_info": "my_important_data",
    "sync_mode": "all",
    "filter_namespace_white": "mcd"
}'
```


运行环境
-------
- 服务端
```
-- run运行环境
python: 3.10.14

OS: Linux
Arch: x86_64
Distribution: CentOS7.8
```
- 客户端
```
python: 3.10.14
```

