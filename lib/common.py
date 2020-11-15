from fabric.api import put, run, get, cd
from fabric.contrib.files import exists
import json
import os
import time
from fabric.colors import *

status_message = {
    'wget_error_message': '未安装wget相关组件，开始安装',
    'docker_error_message': 'docker未安装，开始安装',
    'firewall_error_message': '防火墙未关闭，执行关闭',
    'file_exist': '文件存在，跳过拉取文件步骤'
}

download_address = {
    # kubernetes server压缩包 v1.18
    'kubernetes_address': 'https://dl.k8s.io/v1.18.3/kubernetes-server-linux-amd64.tar.gz',
    # CNI压缩包,v0.8.6
    'cni_address': 'https://github.com/containernetworking/plugins/releases/download/v0.8.6/cni-plugins-linux-amd64-v0.8.6.tgz',
    # flannel压缩包, v0.12.0
    'flannel_address': 'https://github.com/coreos/flannel/releases/download/v0.12.0/flannel-v0.12.0-linux-amd64.tar.gz',
    # etcd 压缩包 v3.4.9
    'etcd_address': 'https://github.com/etcd-io/etcd/releases/download/v3.4.9/etcd-v3.4.9-linux-amd64.tar.gz'
}

with open('address.json', 'r') as f:
    data = json.loads(f.read())
    for i in data:
        if data[i]:
            download_address[i] = data[i]


def exec_shell(shell_path, filename):
    # 上传及执行shell,执行完毕删除的方法
    put(f"{shell_path}/{filename}", '/root')
    run(f"chmod +x {filename}")
    run(f"bash {filename}")
    run(f"rm -vf {filename}")


# clear files
def clear_cache(filename):
    # 清空备份文件夹下所有文件，防止缓存文件冲突
    backup = f"{os.getcwd()}/backup"
    # file_collections = os.listdir(backup)
    is_exists = f"{backup}/{filename}"
    if os.path.exists(is_exists):
        os.remove(is_exists)
    else:
        print('文件不存在，暂无可删除的备份文件')


def unpack(file_path, file_name, file_list='./*'):
    clear_cache(file_name)
    with cd(file_path):
        run(f'tar zcvf {file_name} {file_list}')
        get(f'./{file_name}', 'backup/')
        if exists(f'{file_path}{file_name}'):
            run(f'rm -rf {file_path}{file_name}')


def approve_cert():
    # 等待启动缓冲
    time.sleep(20)
    csr_cert = run("kubectl get csr | awk 'NR > 1 {print $1}'")
    csr_list = csr_cert.split("\r\n")
    for item in csr_list:
        certificate_status = run(f'kubectl certificate approve {item}')
        if certificate_status.failed:
            print(red('批准证书失败，脚本停止'))
            exit(1)
