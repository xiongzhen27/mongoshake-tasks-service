功能支持
-------
### mongoshake2.4.6  
| 原版本      | 目标版本     | 是否支持 | 支持模式     |
| ----------- ----------- --- |--------------------|
| 3.6    | 3.6 |  是  |  full incr all |
| 3.6    | 4.2 |  是  |  full incr all |
| 4.2    | 4.2 |  是  |  full incr all |

### mongoshake2.8.4
| 原版本      | 目标版本     | 是否支持 | 支持模式     |
| ----------- ----------- --- |--------------------|
| 4.2     | 4.2 |  是  |  full incr all |
| 4.2     | 4.2 |  是  |  full incr all |
| 6.0     | 6.0 |  是  |  full incr all |


参数说明
-------
### 请求地址
http://127.0.0.1:5000/create_task

### 请求类型
POST

### 请求参数
| 参数名      | 类型     | 必填 | 描述                 | 默认值   | 参考值         |
| ----------- |--------| --- |--------------------|-------|-------------|
| shake_version     | string |  是  | 使用的mongoshake二进制版本 | 2.8.4 | 2.4.6｜2.8.4 |
| source_addr | string |  是  | 原mongo集群地址信息       | -     | -           |
| target_addr       | string |  是  | 目标mongo集群地址信息      | -     | -           |
| business_info       | string |  是  | 同时进程标识             | -     | -           |
| sync_mode       | string |  是  | all full  incr     | -     | -          |
| filter_namespace_white       | string |  是  | 过滤白名单              | -     | -           |


