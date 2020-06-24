import logging
from functools import wraps
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.utils import abort
from fabric.colors import *
from fabric.contrib.files import exists, append
import os
import json
import sys
import hashlib
from log import *
logger = logging.getLogger("file")
hostsLists = []


def set_configure(value, key):
    for nodes in value:
        passwords_keys = {f"{nodes['user']}@{nodes['host']}:{nodes.get('port') or 22}": f"{str(nodes['password'])}"}
        env.node_roles[key].append(nodes['host'])
        env.hosts.append(nodes['host'])
        env.passwords.update(passwords_keys)
        hostsLists.append(nodes['host'])


def roles(*params):
    def wrapper(func):
        @wraps(func)
        def inner(*args):
            with open(f'{os.getcwd()}/config.json') as f:
                data = json.loads(f.read())
                for i in params:
                    if i in data.keys():
                        env.hosts = []
                        env.passwords = {}
                        env.warn_only = True
                        env.connection_attempts = 3
                        # 并行执行
                        env.parallel = False
                        env.node_roles = {
                            "master": [],
                            "node": []
                        }
                        env.roledefs = env.node_roles
                        env.current_roles = params
                        # 配置fabric 基本配置
                        set_configure(data[i], i)
                    else:
                        abort('装饰器传入参数无法匹配')
            func(*args)
        return inner

    return wrapper


def ignore(name):
    def wrapper(func):
        @wraps(func)
        def inner(*args):
            print(cyan('主机 {}: 正在进行 {}'.format(env.host, name)))
            logger.info('主机 {}: 正在进行 {}'.format(env.host, name))
            md5 = hashlib.md5()
            md5.update(env.host.encode('utf8'))
            md5.update(func.__name__.encode('utf8'))
            tmp_steps = f'{os.getcwd()}/hash'
            md5_files = os.path.join(tmp_steps, md5.hexdigest())
            logger.info(f'md5: {md5.hexdigest()}, Re-execute, delete this md5, dir: /hash')
            if not os.path.exists(tmp_steps):
                os.mkdir(tmp_steps)
            if not os.path.exists(md5_files):
                logger.info('md5值不存在，开始执行部署任务')
                os.mkdir(md5_files)
            else:
                print(f'跳过步骤: {name}')
                logger.info(f'跳过步骤: {name}')
                return

            func(*args)
        return inner
    return wrapper


class RemoteController:
    def __init__(self, host, user, password):
        env.warn_only = True
        env.host_string = host
        env.password = password
        env.user = user


