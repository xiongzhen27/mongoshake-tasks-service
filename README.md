#### mongoshake-tasks-manager

快速使用
-------
- 服务端
```shell
nohup  python Mongo_Shake_Task_Run.py &
```
- 客户端
Linux/macOS (curl):

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
Linux/macOS (python):
```
python create_mongoshake_task.py
```

运行环境
-------
- 服务端
```
python: 3.10.14

OS: Linux
Arch: x86_64
Distribution: CentOS7.8
```
- 客户端
```
python: 3.10.14
```

