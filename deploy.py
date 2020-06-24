from Controller.RemoteController import *
import time

# 资源下载地址,可配置
# ================================================================================
'''
k8s 1.18需要版本:
    etcd: v3.4.9
    kubernetes bin: v1.18.3
    cni: v0.8.6
    flannel: v0.12.0
'''
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
# ================================================================================

status_message = {
    'wget_error_message': '未安装wget相关组件，开始安装',
    'docker_error_message': 'docker未安装，开始安装',
    'firewall_error_message': '防火墙未关闭，执行关闭'
}

# ================================================================================
# public methods


def exec_shell(shell_path, filename):
    # 上传及执行shell,执行完毕删除的方法
    put(f"{shell_path}/{filename}", '/root')
    run(f"chmod +x {filename}")
    run(f"bash {filename}")
    run(f"rm -vf {filename}")


def init_env():
    with open('config.json', 'r') as f:
        data = json.loads(f.read())
        for i in data:
            for item in data[i]:
                if item['host'] == env.host:
                    env.hostname = item['hostname']
                    env.current_host = item['host']
                    env.user = item['user']
                    env.password = item['password']


def init_directory():
    backup = f"{os.getcwd()}/backup"
    tmp = f"{os.getcwd()}/tools/tmp"
    dir_list = [backup, tmp]
    for i in dir_list:
        if not os.path.exists(i):
            os.mkdir(i)


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


# ================================================================================


@roles('master')
def deploy(exec_task):
    execute(exec_task)


@roles('node')
def deploy_node(exec_task):
    if env.roledefs['node']:
        execute(exec_task)
    else:
        pass


# master task
class DeployTask:
    def __init__(self):
        pass

    def main(self):
        init_env()
        init_directory()
        print(yellow(f"{env.hostname} perform tasks"))
        # check required components
        self.required_components()
        # check requirement
        self.requirement()
        # install etcd components
        deploy_etcd = DeployEtcd()
        deploy_etcd.install_etcd()
        # install api-server components
        deploy_apiserver = DeployApiServer()
        deploy_apiserver.install_apiserver()
        # install manager components
        deploy_manager()
        # install scheduler components
        deploy_scheduler()
        # install kubelet components
        deploy_kubelet()
        # install kube-proxy components
        deploy_kube_proxy()
        # install flanneld components
        deploy_flanneld = DeployFlanneld()
        deploy_flanneld.install_flanneld()
        # modify the docker service file
        update_docker()
        # unpack
        unpack_components()
        # clear generate md5
        # clearInformation()
        print(green('master节点部署完毕'))

    @ignore(u'安装必要组件')
    def required_components(self):
        wget_status = run('wget --version', quiet=True)
        if wget_status.failed:
            print(blue(status_message['wget_error_message']))
            run('yum install -y wget')
        docker_status = run('docker -v', quiet=True)
        if docker_status.failed:
            print(blue(status_message['docker_error_message']))
            print('拉取docker-ce repo文件')
            run(
                'wget https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo')
            print('执行安装docker命令')
            run('yum install -y docker-ce')
            run('systemctl start docker')
            run('systemctl enable docker')
            run('systemctl status docker')
        # 时间同步
        print(blue('设置时间同步'))
        run('yum install ntpdate -y')
        run('timedatectl set-timezone Asia/Shanghai')
        run('ntpdate time.windows.com')

    @ignore(u'配置环境所需条件')
    def requirement(self):
        config_hosts = ''
        template_host = ''
        with open('config.json', 'r') as files:
            all_data = json.loads(files.read())
            for keys in all_data:
                for item in all_data[keys]:
                    config_hosts += f"{item['host']} {item['hostname']}\n"
        with open('tools/env/hosts.default', 'r') as file:
            for lines in file.readlines():
                template_host += lines.format(config_hosts)

        with open('tools/tmp/hosts.sh', 'w') as template_env_host:
            template_env_host.write(template_host)
            template_env_host.close()

        exec_shell('tools/tmp', 'hosts.sh')

        firewall_status = run('systemctl status firewalld', quiet=True)
        if firewall_status.succeeded:
            print(blue(status_message['firewall_error_message']))
            run('systemctl stop firewalld')
            run('systemctl disable firewalld')
        self.set_hostname()
        exec_shell('tools/env', 'env.sh')
        reboot()

    @ignore(u'设置主机名')
    def set_hostname(self):
        run(f"hostnamectl set-hostname {env.hostname}")
        hostname = run('hostname')
        print(blue(f"hostname: {hostname}"))
        time.sleep(1)


# node task
class DeployNodeTask:
    def __init__(self):
        self.master_host = ""
        self.master_list = []
        with open('config.json', 'r') as f:
            data = json.loads(f.read())
            for i in data['master']:
                self.master_list.append(i)
                self.master_host = i['host']

    def main(self):
        init_env()
        init_directory()
        print(yellow(f"{env.hostname} perform tasks"))
        # check required components
        deploy_task_handle = DeployTask()
        deploy_task_handle.required_components()
        # check requirement
        deploy_task_handle.requirement()
        # install node kubelet
        self.node_kubelet_components()
        self.node_create_kubelet()
        self.node_kubelet_approve()
        # install node kube-proxy
        self.node_proxy_components()
        self.node_proxy_start()
        # install flanneld
        self.node_flanneld_components()
        # update docker
        update_docker()
        print(green('node节点部署完毕'))

    @ignore(u'创建kubelet')
    def node_create_kubelet(self):
        put('tools/kubelet/template/kubelet-config.yml', '/opt/kubernetes/cfg')
        template_data = ""
        with open('tools/kubelet/template/create_kubelet_config.default', 'r') as f:
            for line in f.readlines():
                template_data += line.format(env.hostname, self.master_host)
            file = open(f'tools/tmp/create_kubelet_service_{env.hostname}.sh', 'w')
            file.write(template_data)
            file.close()

        exec_shell('tools/tmp', f'create_kubelet_service_{env.hostname}.sh')

    @ignore(u'安装kubelet组件')
    def node_kubelet_components(self):
        is_exists = f"{os.getcwd()}/backup/kubernetes-bin.tar.gz"
        put('backup/kubernetes-token.tar.gz', '/root')
        run('tar zxvf kubernetes-token.tar.gz -C /opt/kubernetes/cfg/')
        put('backup/kubernetes-ssl.tar.gz', '/root')
        run('tar zxvf kubernetes-ssl.tar.gz -C /opt/kubernetes/ssl/')
        put('backup/kubernetes-kubectl.tar.gz', '/root')
        run('tar zxvf kubernetes-kubectl.tar.gz -C /usr/bin/')
        if os.path.exists(is_exists):
            put('backup/kubernetes-bin.tar.gz', '/root')
            run('tar zxvf kubernetes-bin.tar.gz -C /opt/kubernetes/bin/')
        else:
            print(red('文件不存在，无法继续安装'))
            exit(1)

    @ignore(u'批准node csr申请')
    def node_kubelet_approve(self):
        for i in self.master_list:
            RemoteController(i['host'], i['user'], i['password'])
            approve_cert()

    @ignore(u'创建kube-proxy组件')
    def node_proxy_components(self):
        RemoteController(env.host, env.user, env.password)
        put('tools/kube-proxy/template/kube-proxy.conf', '/opt/kubernetes/cfg')
        put('backup/kubernetes-proxy.tar.gz', '/root')
        run('tar zxvf kubernetes-proxy.tar.gz -C /opt/kubernetes/cfg/')
        put('tools/kube-proxy/template/kube-proxy.service', '/usr/lib/systemd/system')

    @ignore(u'启动kube-proxy服务')
    def node_proxy_start(self):
        run('systemctl daemon-reload')
        run('systemctl enable kube-proxy')
        run('systemctl start kube-proxy')
        run('systemctl status kube-proxy')

    @ignore(u'node部署flanneld')
    def node_flanneld_components(self):
        put('backup/etcd.tar.gz', '/root')
        run('tar zxvf etcd.tar.gz -C /opt/etcd/ssl/')
        deploy_node_flanneld = DeployFlanneld()
        deploy_node_flanneld.deploy_flanneld_components(False)
        exec_shell('tools/tmp', 'create_flanneld_service.sh')


# deploy etcd
class DeployEtcd:
    initial_cluster = ''

    def __init__(self):
        self.backup = f"{os.getcwd()}/backup"
        self.hosts = []
        self.etcd_template = ""
        self.host_list = []
        with open('config.json', 'r') as f:
            data = json.loads(f.read())
            for i in data:
                for host_item in data[i]:
                    self.host_list.append(host_item)

    @ignore(u'生成etcd证书')
    def generate_etcd_cert(self):
        run('mkdir -p ~/TLS/{etcd,k8s}')
        # 清空备份文件夹下所有文件，防止缓存文件冲突
        file_collections = os.listdir(self.backup)
        for file in file_collections:
            os.remove(f"{self.backup}/{file}")

        print(yellow('生成ETCD证书'))
        # 读取模板文件，写入host配置并 put server
        # 读取config.json，取出所有配置拼接生成
        with open('config.json', 'r') as f:
            data = json.loads(f.read())
            for item in data['master']:
                self.hosts.append(item['host'])
            # TODO 暂时取消集群安装ETCD
            # for item in data:
            #     for i in data[item]:
            #         self.hosts.append(i['host'])
        with open('tools/etcd/template/etcd-template.default', 'r') as f:
            for line in f.readlines():
                self.etcd_template += line.format(json.dumps(self.hosts))
        with open('tools/tmp/server-csr.json', 'w')as file:
            file.truncate()
            file.write(self.etcd_template)
            file.close()
        put('tools/tmp/server-csr.json', '/root/TLS/etcd/')
        # 默认从本地上传
        cfssl_path = ['/usr/local/bin/cfssl', '/usr/local/bin/cfssljson', '/usr/bin/cfssl-certinfo']
        cfssl_local_path = ['tools/bin/cfssl_linux-amd64', 'tools/bin/cfssljson_linux-amd64',
                            'tools/bin/cfssl-certinfo_linux-amd64']
        exists = True
        for i in cfssl_path:
            if not os.path.exists(i):
                exists = False
        if not exists:
            for i in cfssl_local_path:
                put(i, '/root')

        # 上传并执行生成证书脚本
        exec_shell('tools/etcd', 'gencert.sh')
        # 备份远程生成etcd证书压缩包至本地
        get('/opt/etcd/ssl/etcd.tar.gz', 'backup/')
        get('/opt/etcd/etcd-all.tar.gz', 'backup/')

    @ignore(u'拉取etcd必要组件')
    def deploy_etcd_components(self):
        run(f"wget {download_address['etcd_address']}")
        exec_shell('tools/etcd', 'install_etcd.sh')

    def configure_etcd(self, template_path, hostname, host):
        # 读取config.json，取出所有配置拼接生成
        with open('config.json', 'r') as f:
            data = json.loads(f.read())
            for item in data['master']:
                self.initial_cluster += f"{item['hostname']}=https://{item['host']}:2380"
                # TODO 暂时取消集群部署ETCD
                # for i in data[item]:
                #     self.initial_cluster += f"{i['hostname']}=https://{i['host']}:2380,"

        # 读取模板文件，写入sh文件，生成etcd配置文件
        file_data = ""
        # 'tools/etcd/template/etcd.config.default'
        with open(template_path, 'r') as f:
            for line in f.readlines():
                file_data += line.format(hostname, host, self.initial_cluster.rstrip(','))

        # 写入配置文件
        with open(f'tools/tmp/etcd.config-{hostname}.sh', 'w') as f:
            f.write(file_data)
            f.close()
            self.initial_cluster = ''

    @ignore(u'安装etcd')
    def install_etcd(self):
        # TODO 方法待优化
        print(blue('部署ETCD'))
        # 签发etcd证书 (generate cert)
        self.generate_etcd_cert()
        time.sleep(1)

        # 读取配置文件是否集群模式(is cluster?)
        # 根据配置生成模板 (generate templates based on config)
        self.configure_etcd('tools/etcd/template/etcd.config.default', env.hostname, env.current_host)
        # 执行安装etcd
        self.deploy_etcd_components()

        # TODO 生成以主机名脚本，方便以后扩展集群Etcd
        exec_shell('tools/tmp', f'etcd.config-{env.hostname}.sh')
        run('systemctl daemon-reload')
        run('systemctl enable etcd')
        run('systemctl start etcd')
        run('systemctl status etcd')
        print(green('ETCD部署完毕'))


# deploy kube-apiserver
class DeployApiServer:
    def __init__(self):
        self.backup = f"{os.getcwd()}/backup"
        self.apiServerFile = f"{self.backup}/apiServer.tar"
        if os.path.exists(self.apiServerFile):
            os.remove(self.apiServerFile)

    @ignore(u'部署apiserver组件')
    def deploy_apiserver_components(self):
        path_pre = "kubernetes/server/bin"
        run(f"wget {download_address['kubernetes_address']}")
        run('tar zxvf kubernetes-server-linux-amd64.tar.gz')
        run(
            f'cp {path_pre}/kube-apiserver {path_pre}/kube-scheduler {path_pre}/kube-controller-manager {path_pre}/kubelet {path_pre}/kube-proxy /opt/kubernetes/bin')
        run(f'cp {path_pre}/kubectl /usr/bin')
        print(yellow('验证复制文件是否正常'))
        run('ls /opt/kubernetes/bin')

    @ignore(u'配置apiserver证书')
    def config_secert(self):
        # master
        # 创建api-server秘钥文件，并写入json文件
        with open('tools/apiServer/template/apiserver-template.json', 'r') as f:
            template_data = json.loads(f.read())
            with open('config.json', 'r') as files:
                data = json.loads(files.read())
                for item in data:
                    for i in data[item]:
                        template_data['hosts'].append(i['host'])
            file = open('tools/tmp/apiserver-csr.json', 'w')
            file.truncate()
            file.write(json.dumps(template_data))
            file.close()
        # 上传秘钥json文件
        put('tools/tmp/apiserver-csr.json', '/root/TLS/k8s')
        # 生成证书
        print(yellow('生成基础证书'))
        put('tools/apiServer/template/ca-config.json', '/root/TLS/k8s')
        put('tools/apiServer/template/ca-csr.json', '/root/TLS/k8s')
        with cd('/root/TLS/k8s'):
            run('cfssl gencert -initca ca-csr.json | cfssljson -bare ca -')
            run(
                'cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes apiserver-csr.json | cfssljson -bare server')
        run('cp ~/TLS/k8s/ca*pem ~/TLS/k8s/server*pem /opt/kubernetes/ssl/')
        with cd('/opt/kubernetes/ssl'):
            run('tar zcvf apiServer.tar ./*')
        # 备份远程生成api-server证书压缩包至本地
        get('/opt/kubernetes/ssl/apiServer.tar', 'backup/')

    @ignore(u'生成kube-apiserver service文件')
    def create_apiserver_service(self):
        # 模板文件变量
        data = ""
        # 拼接etcd地址
        etcd_servers = ""
        # 获取所有的host
        # 读取config.json，取出所有配置拼接生成
        with open('config.json', 'r') as f:
            datas = json.loads(f.read())
            for item in datas['master']:
                etcd_servers += f"https://{item['host']}:2379"
                # TODO 暂时取消集群安装ETCD
                # for i in datas[item]:
                #     etcd_servers += f"https://{i['host']}:2379,"

        # 读取模板文件
        with open('tools/apiServer/template/kube-apiserver.default', 'r') as f:
            for line in f.readlines():
                # format: 当前节点，etcd地址
                data += line.format(env.current_host, etcd_servers.rstrip(','))

            file = open('tools/apiServer/create_service.sh', 'w')
            file.write(data)
            file.close()

        # 生成service
        exec_shell('tools/apiServer', 'create_service.sh')

    @ignore(u'安装kube-apiserver')
    def install_apiserver(self):
        self.config_secert()
        self.deploy_apiserver_components()
        exec_shell('tools/apiServer', 'create_token.sh')
        self.create_apiserver_service()
        run('systemctl daemon-reload')
        run('systemctl enable kube-apiserver')
        run('systemctl start kube-apiserver')
        run('systemctl status kube-apiserver')
        time.sleep(20)
        print(yellow('授权kubelet-bootstrap用户允许请求证书'))
        run('/usr/bin/kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap')
        run('/usr/bin/kubectl create clusterrolebinding kube-apiserver:kubelet-apis --clusterrole=system:kubelet-api-admin --user kubernetes')
        print(green('api-server部署完毕'))


# deploy kube controller manager
@ignore(u'部署kube-controller-manager')
def deploy_manager():
    print(blue('部署kube-controller-manager'))
    exec_shell('tools/controller-manager', 'install_controller-manager.sh')
    print(green('kube-controller-manager部署完毕'))


# deploy scheduler
@ignore(u'部署kube-scheduler')
def deploy_scheduler():
    print(blue('部署kube-scheduler'))
    exec_shell('tools/scheduler', 'install_scheduler.sh')
    print(green('kube-scheduler部署完毕'))


def approve_cert():
    # 等待启动缓冲
    time.sleep(20)
    csr_cert = run("kubectl get csr | awk 'NR > 1 {print $1}'")
    csr_list = csr_cert.split("\r\n")
    for i in csr_list:
        certificate_status = run(f'kubectl certificate approve {i}')
        if certificate_status.failed:
            print(red('批准证书失败，脚本停止'))
            exit(1)


# deploy kubelet
@ignore(u'部署kubelet')
def deploy_kubelet():
    put('tools/kubelet/template/kubelet-config.yml', '/opt/kubernetes/cfg')
    template_data = ""
    with open('tools/kubelet/template/create_kubelet_config.default', 'r') as f:
        for line in f.readlines():
            template_data += line.format(env.hostname, env.host)
        file = open(f'tools/tmp/create_kubelet_service_{env.hostname}.sh', 'w')
        file.write(template_data)
        file.close()

    exec_shell('tools/tmp', f'create_kubelet_service_{env.hostname}.sh')
    # 批准证书
    approve_cert()


# deploy kube-proxy
@ignore(u'部署kube-proxy')
def deploy_kube_proxy():
    # 清理备份文件
    clear_cache('kube-proxy.tar.gz')
    template_data = ""
    with open('tools/kube-proxy/template/kube-proxy-config.default', 'r') as f:
        for i in f.readlines():
            template_data += i.format(env.hostname, env.host)
        file = open('tools/tmp/create_kube-proxy_config.sh', 'w')
        file.write(template_data)
        file.close()

    # 上传文件
    put('tools/kube-proxy/template/kube-proxy.conf', '/opt/kubernetes/cfg')
    put('tools/kube-proxy/template/kube-proxy-csr.json', '/root/TLS/k8s')
    # 签发证书
    with cd('/root/TLS/k8s'):
        run(
            'cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes kube-proxy-csr.json | cfssljson -bare kube-proxy')
        run('ls kube-proxy*pem')
        run('tar zcvf kube-proxy.tar.gz kube-proxy*pem')
        get('/root/TLS/k8s/kube-proxy.tar.gz', 'backup/')

    # 执行生成脚本，生成配置文件及kube-proxy配置文件等
    exec_shell('tools/tmp', 'create_kube-proxy_config.sh')
    # 拷贝生成配置文件到指定目录
    run('cp /root/kube-proxy.kubeconfig /opt/kubernetes/cfg/')
    # 上传kube-proxy service文件
    put('tools/kube-proxy/template/kube-proxy.service', '/usr/lib/systemd/system')
    # 开启服务
    run('systemctl daemon-reload')
    run('systemctl stop kube-proxy')
    run('systemctl start kube-proxy')
    run('systemctl enable kube-proxy')
    run('systemctl status kube-proxy')
    print(green('kube-proxy部署完毕'))


# deploy flanneld
class DeployFlanneld:
    def __init__(self):
        self.etcd_endpoints = ""
        self.network = ""

    @ignore(u'处理压缩包')
    def deploy_flanneld_components(self, master_run=True):
        # CNI压缩包处理
        run(f"wget {download_address['cni_address']}")
        print(yellow('创建CNI目录'))
        run('mkdir -p /opt/cni/bin')
        print(yellow('解压CNI压缩包'))
        # 修改名称，防止解压失败
        # run('mv cni*.tgz cni-plugins.tgz')
        run('tar zxvf cni-plugins-linux-amd64-v0.8.6.tgz -C /opt/cni/bin')
        # flannel压缩包处理
        run(f"wget {download_address['flannel_address']}")
        # 修改名称，防止解压失败
        # run('mv flannel*.tar.gz flannel.tar.gz')
        run('tar zxvf flannel-v0.12.0-linux-amd64.tar.gz')
        run('cp flanneld mk-docker-opts.sh /usr/local/bin/')
        if master_run:
            self.precondition()
        else:
            pass

    @ignore(u'配置flanneld网络信息')
    def precondition(self):
        # 读取config.json，取出所有配置拼接生成
        with open('config.json', 'r') as f:
            data = json.loads(f.read())
            for item in data['master']:
                self.etcd_endpoints += f"https://{item['host']}:2379"
                # TODO 暂时取消集群安装ETCD
                # for i in data[item]:
                #     self.etcd_endpoints += f"https://{i['host']}:2379,"

        # 写入网段信息，网段与controller-manager网段保持一致
        # flanneld 不支持 etcd 3.4版本后的读写方式，两种方式:
        # 1. 将etcd降级为3.3.10,默认v2版本写入
        # 2. 将etcd以api v2版本启动，以v2版本写入网段信息 (这里采用这种)
        '''
        ETCDCTL_API=2  ./etcdctl --ca-file=/opt/etcd/ssl/ca.pem \
          --cert-file=/opt/etcd/ssl/server.pem \
          --key-file=/opt/etcd/ssl/server-key.pem \
          --endpoints="https://${CLUSER_IP}:2379" \
          set /coreos.com/network/config  \
         '{ "Network": "10.244.0.0/16", "Backend": {"Type": "vxlan"}}'
        '''
        print(yellow('向ETCD写入网段信息'))
        # 拼接写入etcd网段信息命令
        with open('tools/flanneld/template/network.config.default', 'r') as f:
            for i in f.readlines():
                self.network += i.format(self.etcd_endpoints.rstrip(","))
            file = open('tools/tmp/create_flanneld_network.sh', 'w')
            file.write(self.network)
            file.close()

        exec_shell('tools/tmp', 'create_flanneld_network.sh')

    @ignore(u'创建flanneld服务')
    def create_flanneld_service(self):
        template_data = ""
        with open('tools/flanneld/template/flanneld.config.default', 'r') as f:
            for i in f.readlines():
                template_data += i.format(self.etcd_endpoints.rstrip(","))
            file = open('tools/tmp/create_flanneld_service.sh', 'w')
            file.write(template_data)
            file.close()
        exec_shell('tools/tmp', 'create_flanneld_service.sh')

    @ignore(u'安装flanneld服务')
    def install_flanneld(self):
        self.deploy_flanneld_components()
        self.create_flanneld_service()
        print(green('flanneld部署完毕'))


# modify the docker service file
@ignore(u'指定docker子网段')
def update_docker():
    print(yellow('注释docker service ExecStart字段'))
    run("sed -i 's/ExecStart/#&/' /usr/lib/systemd/system/docker.service")
    print(yellow('新增docker service字段，指定子网段'))
    run("sed -i '/#ExecStart/a EnvironmentFile=/run/flannel/docker' /usr/lib/systemd/system/docker.service")
    run(
        "sed -i '/EnvironmentFile/a ExecStart=/usr/bin/dockerd $DOCKER_NETWORK_OPTIONS' /usr/lib/systemd/system/docker.service")
    print(yellow('重启docker service'))
    run('systemctl daemon-reload')
    run('systemctl restart docker')
    run('systemctl start docker')
    run('systemctl status docker')
    run('ip -4 a')


# clear information
def clearInformation():
    file_hash = f"{os.getcwd()}/hash"
    file_collections = os.listdir(file_hash)
    if os.path.exists(file_hash):
        for i in file_collections:
            os.removedirs(f"{file_hash}/{i}")


# unpack
@ignore(u'备份组件')
def unpack_components():
    pass
    # 打包kubelet, kube-proxy 二进制文件
    unpack('/opt/kubernetes/bin/', 'kubernetes-bin.tar.gz', './kubelet ./kube-proxy')
    # 打包kubectl
    unpack('/usr/bin/', 'kubernetes-kubectl.tar.gz', './kubectl')
    # 打包cfg文件
    unpack('/opt/kubernetes/cfg/', 'kubernetes-token.tar.gz', 'token.csv --exclude kubelet-client*')
    # 打包ssl文件
    unpack('/opt/kubernetes/ssl/', 'kubernetes-ssl.tar.gz', '--exclude=kubelet-client* ./*')
    # 打包kube-proxy文件
    unpack('/opt/kubernetes/cfg/', 'kubernetes-proxy.tar.gz', './kube-proxy.kubeconfig ./kube-proxy-config.yml')


if __name__ == '__main__':
    # 部署master节点
    deploy_task = DeployTask()
    deploy(deploy_task.main)
    # 部署node节点
    deploy_node_task = DeployNodeTask()
    deploy_node(deploy_node_task.main)
