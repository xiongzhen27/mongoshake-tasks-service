# -*- coding: UTF-8 -*-
import os
import shutil
import subprocess
import time
import random
import string
from flask import Flask, request, jsonify
from jinja2 import Environment, FileSystemLoader  # 导入 Jinja2

app = Flask(__name__)

# Base configuration
TASKS_BASE_DIR = "/data/mongoshake/sync_tasks"
TEMPLATE_DIR = "./template"
OUTPUT_CONFIG_NAME = "mongo_shake.conf"  # Output config file name

# 定义不同版本的配置
SHAKE_VERSIONS = {
    "2.4.6": {
        "binary": "./tools/collector.linux_2_4_6",
        "template": "template/shake_2.4.6_conf.tmp.j2"  # 使用 .j2 扩展名
    },
    "2.8.4": {
        "binary": "./tools/collector.linux_2_8_4",
        "template": "template/shake_2.8.4_conf.tmp.j2"  # 使用 .j2 扩展名
    }
}

# Port range configuration
# PORT_RANGES = {
#     "full_sync": (2000, 2100),
#     "incr_sync": (3000, 3100),
#     "system_profile": (29000, 29100)
# }
#
# # Track used ports
# used_ports = {
#     "full_sync": set(),
#     "incr_sync": set(),
#     "system_profile": set()
# }

PORT_BASES = {
    "full_sync": 2000,
    "incr_sync": 3000,
    "system_profile": 29000
}

used_offsets = set()

def get_available_ports():
    """Get a set of three correlated ports (full_sync, incr_sync, system_profile)"""
    max_offset = 100  # Maximum offset from base port
    available_offsets = set(range(0, max_offset + 1)) - used_offsets

    # Try random offset first
    if available_offsets:
        for _ in range(50):
            offset = random.choice(list(available_offsets))
            full_port = PORT_BASES["full_sync"] + offset
            incr_port = PORT_BASES["incr_sync"] + offset
            system_port = PORT_BASES["system_profile"] + offset

            # Check if all ports are actually available
            if all(check_port_available(port) for port in (full_port, incr_port, system_port)):
                used_offsets.add(offset)
                return full_port, incr_port, system_port

    # Fallback to sequential search
    for offset in range(0, max_offset + 1):
        if offset not in used_offsets:
            full_port = PORT_BASES["full_sync"] + offset
            incr_port = PORT_BASES["incr_sync"] + offset
            system_port = PORT_BASES["system_profile"] + offset

            if all(check_port_available(port) for port in (full_port, incr_port, system_port)):
                used_offsets.add(offset)
                return full_port, incr_port, system_port

    raise RuntimeError("No available port offsets in range 0-100")


def check_port_available(port):
    """Check if a port is actually available on the system"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False



# 创建 Jinja2 环境
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def generate_random_string(length=20):
    """生成指定长度的随机字符串（只包含小写字母和数字）"""     # 只使用小写字母和数字
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_available_port(port_type):
    """Get available port for specified type"""
    min_port, max_port = PORT_RANGES[port_type]
    used = used_ports[port_type]

    # Try random port first
    for _ in range(50):
        port = random.randint(min_port, max_port)
        if port not in used:
            used.add(port)
            return port

    # Fallback to sequential search
    for port in range(min_port, max_port + 1):
        if port not in used:
            used.add(port)
            return port

    raise RuntimeError(f"No available {port_type} port in range {min_port}-{max_port}")


def release_port(port_type, port):
    """Release a port"""
    if port in used_ports[port_type]:
        used_ports[port_type].remove(port)


@app.route('/create_task', methods=['POST'])
def create_task():
    # Parse request parameters
    data = request.json
    source_addr = data.get('source_addr')
    target_addr = data.get('target_addr')
    business_info = data.get('business_info', 'default_task')
    sync_mode = data.get('sync_mode', 'all')  # Default: full + incremental sync
    filter_namespace_white = data.get('filter_namespace_white')

    # 获取 shake_version 参数，默认为 "2.8.4"
    shake_version = data.get('shake_version', '2.8.4')

    # 验证 shake_version 是否有效
    if shake_version not in SHAKE_VERSIONS:
        return jsonify({"error": f"Invalid shake_version. Supported versions: {', '.join(SHAKE_VERSIONS.keys())}"}), 400

    # 获取对应版本的配置
    version_config = SHAKE_VERSIONS[shake_version]
    collector_binary = version_config["binary"]
    config_template_file = version_config["template"]

    # Validate sync mode
    if sync_mode not in ['all', 'full', 'incr']:
        return jsonify({"error": "Invalid sync_mode. Must be 'all', 'full' or 'incr'"}), 400

    if not source_addr or not target_addr:
        return jsonify({"error": "Source and target_addr clusters are required"}), 400

    # try:
    #     # Get available ports
    #     # full_port = get_available_port("full_sync")
    #     # incr_port = get_available_port("incr_sync")
    #     # system_port = get_available_port("system_profile")
    #
    # except RuntimeError as e:
    #     return jsonify({"error": str(e)}), 500

    try:
        full_port, incr_port, system_port = get_available_ports()
        print(f"Allocated ports: Full Sync: {full_port}, Incr Sync: {incr_port}, System Profile: {system_port}")
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    # Create task directory
    current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    task_dir = os.path.join(TASKS_BASE_DIR, f"{current_time}_{business_info}")
    try:
        os.makedirs(task_dir, exist_ok=True)
    except Exception as e:
        # Release allocated ports
        release_port("full_sync", full_port)
        release_port("incr_sync", incr_port)
        release_port("system_profile", system_port)
        return jsonify({"error": f"Failed to create task directory: {str(e)}"}), 500

    try:
        # 生成随机ID和数据库名
        shake_task_id = "mongoshake_" + generate_random_string(20)
        checkpoint_db = shake_task_id

        # 使用 Jinja2 渲染模板
        template = jinja_env.get_template(config_template_file)
        config_content = template.render(
            source_addr=source_addr,
            target_addr=target_addr,
            full_port=full_port,
            incr_port=incr_port,
            system_port=system_port,
            sync_mode=sync_mode,
            shake_task_id=shake_task_id,
            checkpoint_db=checkpoint_db,
            filter_namespace_white=filter_namespace_white  # 传入过滤参数
        )
        OUTPUT_CONFIG_NAME = f"{shake_task_id}.conf"  # Output config file name
        # Write config file
        config_path = os.path.join(task_dir, OUTPUT_CONFIG_NAME)
        with open(config_path, 'w') as f:
            f.write(config_content.strip())
    except Exception as e:
        # Clean up task directory
        shutil.rmtree(task_dir, ignore_errors=True)
        # Release ports
        release_port("full_sync", full_port)
        release_port("incr_sync", incr_port)
        release_port("system_profile", system_port)
        return jsonify({"error": f"Failed to create config: {str(e)}"}), 500

    # Start MongoShake task
    try:
        os.chdir(task_dir)
        cmd = f"nohup {collector_binary} -conf={OUTPUT_CONFIG_NAME} > collector.log 2>&1 &"
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        shutil.rmtree(task_dir, ignore_errors=True)
        release_port("full_sync", full_port)
        release_port("incr_sync", incr_port)
        release_port("system_profile", system_port)
        return jsonify({"error": f"Failed to start task: {str(e)}"}), 500

    # 准备响应数据
    response_data = {
        "status": "success",
        "task_id": f"{current_time}_{business_info}",
        "directory": task_dir,
        "config_path": config_path,
        "ports": {
            "full_sync": full_port,
            "incr_sync": incr_port,
            "system_profile": system_port
        },
        "sync_mode": sync_mode,
        "shake_task_id": shake_task_id,
        "checkpoint_db": checkpoint_db,
        "shake_version": shake_version
    }

    # 如果使用了命名空间过滤，添加到响应中
    if filter_namespace_white:
        response_data["filter_namespace_white"] = filter_namespace_white

    return jsonify(response_data)


if __name__ == '__main__':
    # Ensure base directories exist
    os.makedirs(TASKS_BASE_DIR, exist_ok=True)
    os.makedirs(TEMPLATE_DIR, exist_ok=True)

    app.run(host='0.0.0.0', port=5000, debug=True)
