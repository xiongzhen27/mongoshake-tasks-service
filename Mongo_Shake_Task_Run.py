# -*- coding: UTF-8 -*-
import os
import shutil
import subprocess
import time
import random
import string
import socket  # 添加缺失的模块
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from jinja2 import Environment, FileSystemLoader



# ==================== 日志配置 ====================
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "run_shake.log")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 创建日志记录器
logger = logging.getLogger('MongoShakeManager')
logger.setLevel(logging.DEBUG)

# 创建文件处理器 - 最多保留3个备份，每个最大10MB
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10*1024*1024,
    backupCount=3,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 记录启动信息
logger.info("="*50)
logger.info("MongoShake Task Manager 启动")
logger.info(f"日志文件: {os.path.abspath(LOG_FILE)}")
logger.info("="*50)


app = Flask(__name__)

# Base configuration
TASKS_BASE_DIR = "/data/mongoshake/sync_tasks"
TEMPLATE_DIR = "./template"
CONFIG_FILE_NAME = "mongo_shake.conf"  # 使用常量定义配置文件名

# 定义不同版本的配置
SHAKE_VERSIONS = {
    "2.4.6": {
        "binary": "./tools/collector.linux_2_4_6",
        "template": "shake_2.4.6_conf.tmp.j2"
    },
    "2.8.4": {
        "binary": "./tools/collector.linux_2_8_4",
        "template": "shake_2.8.4_conf.tmp.j2"
    }
}

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


def release_ports_by_offset(full_port):
    """Release ports by the full_sync port"""
    offset = full_port - PORT_BASES["full_sync"]
    if offset in used_offsets:
        used_offsets.remove(offset)
        print(f"Released offset: {offset}")


# 创建 Jinja2 环境
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_random_string(length=20):
    """生成指定长度的随机字符串（只包含小写字母和数字）"""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


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
        # Release allocated ports by offset
        release_ports_by_offset(full_port)
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
            filter_namespace_white=filter_namespace_white
        )

        # 使用常量定义的文件名
        config_path = os.path.join(task_dir, CONFIG_FILE_NAME)
        with open(config_path, 'w') as f:
            f.write(config_content.strip())
    except Exception as e:
        # Clean up task directory
        shutil.rmtree(task_dir, ignore_errors=True)
        # Release ports by offset
        release_ports_by_offset(full_port)
        return jsonify({"error": f"Failed to create config: {str(e)}"}), 500

    # Start MongoShake task (不切换当前工作目录)
    try:
        # 使用绝对路径启动进程
        collector_path = os.path.abspath(collector_binary)
        config_path_abs = os.path.abspath(config_path)

        cmd = f"cd {task_dir} && nohup {collector_path} -conf={config_path_abs} > collector.log 2>&1 &"
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        shutil.rmtree(task_dir, ignore_errors=True)
        release_ports_by_offset(full_port)
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
