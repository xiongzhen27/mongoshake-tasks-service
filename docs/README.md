参数说明
-------
### 请求地址
http://127.0.0.1:5000/create_task

### 请求类型
POST

### 请求参数
| 参数名                        | 类型     | 必填 | 描述           | 默认值        | 参考值                               |
|----------------------------|--------|----|--------------|------------|-----------------------------------|
| shake_version              | string | 否  | mongoshake版本 | 2.8.4      | 2.4.6｜2.8.4                       |
| mongo_connect_mode         | string | 否  | mongo连接模式    | secondaryPreferred     | secondaryPreferred｜primary   |
| source_addr                | string | 是  | 原mongo集群地址   | -          | mongodb://admin:xxxxxx@10.10.10.1:27017 |
| target_addr                | string | 是  | 目标mongo集群地址  | -          | mongodb://admin:xxxxxx@10.20.18.1:27017 |
| source_arch                | string | 是  | 原mongo集群架构   | -          | replication｜shard                 |
| target_arch                | string | 是  | 目标mongo集群架构  | -          | replication｜shard                 |
| business_info              | string | 是  | 同步进程标识       | -          | my_important_data                 |
| sync_mode                  | string | 是  | 同步模式         | -          | full  /  incr  /  all             |
| filter_namespace_white     | string | 否  | 过滤白名单db/集合   | 空          | account.user;person.stu           |
| create_index_mode          | string | 否  | 是否创建索引       | background | background  /  foreground  /  none |
| collection_exist_drop_mode | string | 否  | 是否覆盖目标已存在集合  | false      | true  /  false                    |



功能支持
-------
### mongoshake2.4.6  
| 原版本      | 目标版本     | 是否支持 | 支持模式          |
| -----------|-----------|------|---------------|
| 3.6    | 3.6 | 是    | full/incr/all |
| 3.6    | 4.2 | 是    | full/incr/all |
| 4.2    | 4.2 | 是    | full/incr/all |

### mongoshake2.8.4
| 原版本      | 目标版本     | 是否支持 | 支持模式          |
| ----------- |-----------|------|---------------|
| 4.2     | 4.2 | 是    | full/incr/all |
| 4.2     | 4.2 | 是    | full/incr/all |
| 6.0     | 6.0 | 是    | full/incr/all |

