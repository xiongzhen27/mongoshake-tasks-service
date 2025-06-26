#### mongoshake-tasks-manager

快速使用
-------
- 服务端
nohup  python Mongo_Shake_Task_Run.py &

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


服务端运行环境
```
#默认访问HTTP: 5000

shell
-- run运行环境
python: 3.10.14

OS: Linux
Arch: x86_64
Distribution: CentOS7.8
```


