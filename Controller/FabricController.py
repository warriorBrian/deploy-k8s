from functools import wraps
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.utils import abort
from fabric.colors import *
from fabric.contrib.files import exists, append
import os
import json
import sys
import time
import hashlib
from log import *
logger = logging.getLogger("file")

work_pwd = os.path.abspath('../')

env.node_roles = {
    "master": [],
    "node": []
}
env.hosts = []
env.passwords = {}
env.warn_only = True
env.connection_attempts = 3
env.roledefs = env.node_roles
env.hostname = {}
env.data = {}


def set_configure(json_path):
    with open(json_path) as f:
        data = json.loads(f.read())
        env.data = data
        for i in data:
            for item in data[i]:
                env.node_roles[i].append(item['host'])
                password_keys = {f"{item['user']}@{item['host']}:{item.get('port') or 22}": f"{str(item['password'])}"}
                env.passwords.update(password_keys)
                env.hosts.append(item['host'])
                env.user = item['user']
                env.hostname[item['host']] = item['hostname']


def ignore(name):
    def wrapper(func):
        @wraps(func)
        def inner(*args):
            print(cyan('主机 {}: 正在进行 {}'.format(env.host, name)))
            logger.info('主机 {}: 正在进行 {}'.format(env.host, name))
            md5 = hashlib.md5()
            if env.host:
                md5.update(env.host.encode('utf8'))
            md5.update(func.__name__.encode('utf8'))
            tmp_steps = f'{os.getcwd()}/tmp/hash'
            md5_files = os.path.join(tmp_steps, md5.hexdigest())
            logger.info(f'md5: {md5.hexdigest()}, Re-execute, delete this md5, dir: /hash')
            if not os.path.exists(tmp_steps):
                os.makedirs(tmp_steps)
            if not os.path.exists(md5_files):
                logger.info('md5值不存在，开始执行部署任务')
                os.mkdir(md5_files)
            else:
                print(yellow(f'跳过步骤: {name}'))
                logger.info(f'跳过步骤: {name}')
                return

            func(*args)
        return inner
    return wrapper


set_configure(f'{os.getcwd()}/config.json')

if __name__ == '__main__':
    set_configure(f'{work_pwd}/config.json')
