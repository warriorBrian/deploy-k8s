from Controller.FabricController import *
from lib.common import exec_shell, download_address, status_message


class DeployApiServer:
    def __init__(self):
        self.backup = f"{os.getcwd()}/backup"
        self.apiServerFile = f"{self.backup}/apiServer.tar"

    def install(self):
        # pull kubernetes components
        execute(self.pull_main_components)
        # configure kubernetes cert
        execute(self.configure_apiServer_cert)
        # push cert node(only)
        if env.roledefs['node']:
            execute(self.push_apiServer_node_cert)
        # create api-server service
        execute(self.create_apiserver_service)
        # deploy kube-apiserver
        execute(self.deploy_apiserver)

    @roles('master', 'node')
    @ignore(u'部署apiserver组件')
    def pull_main_components(self):
        path_pre = "/root/kubernetes/server/bin"
        master_bin_list = ['kube-apiserver', 'kube-scheduler', 'kube-controller-manager', 'kubelet', 'kube-proxy']
        node_bin_list = ['kubelet', 'kube-proxy']
        if not exists('/root/kubernetes*.tar.gz'):
            run(f"wget {download_address['kubernetes_address']}")
            run('tar zxvf kubernetes*.tar.gz')
        else:
            if not exists('/root/kubernetes'):
                print(blue('压缩包存在，解压'))
                run('tar zxvf kubernetes*.tar.gz')
            else:
                print(blue(status_message['file_exist']))

        if env.host in env.roledefs['master']:
            for kube_bin in master_bin_list:
                if not exists(f'/opt/kubernetes/bin/{kube_bin}'):
                    run(f'cp {path_pre}/{kube_bin} /opt/kubernetes/bin')
            if not exists('/usr/bin/kubectl'):
                run(f'cp {path_pre}/kubectl /usr/bin')
        else:
            for node_bin in node_bin_list:
                if not exists(f'/opt/kubernetes/bin/{node_bin}'):
                    run(f'cp {path_pre}/{node_bin} /opt/kubernetes/bin')
                if not exists('/usr/bin/kubectl'):
                    run(f'cp {path_pre}/kubectl /usr/bin')

        print(yellow('验证复制文件是否正常'))

        run('ls /opt/kubernetes/bin')

    @roles('master')
    @ignore(u'配置apiserver证书')
    def configure_apiServer_cert(self):
        # 清除备份文件
        if os.path.exists(self.apiServerFile):
            os.remove(self.apiServerFile)
        # 创建api-server秘钥文件，并写入json文件
        with open('tools/apiServer/template/apiserver-template.json', 'r') as f:
            template_data = json.loads(f.read())
            template_data['hosts'].extend(env.hosts)
            file = open('tmp/shell/apiserver-csr.json', 'w')
            file.truncate()
            file.write(json.dumps(template_data))
            file.close()

        # 上传秘钥json文件
        put('tmp/shell/apiserver-csr.json', '/root/TLS/k8s')
        # 生成证书
        print(yellow('生成基础证书'))
        put('tools/apiServer/template/ca-config.json', '/root/TLS/k8s')
        put('tools/apiServer/template/ca-csr.json', '/root/TLS/k8s')
        with cd('/root/TLS/k8s'):
            run('cfssl gencert -initca ca-csr.json | cfssljson -bare ca -')
            run('cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes apiserver-csr.json | cfssljson -bare server')
        run('cp /root/TLS/k8s/ca*pem /root/TLS/k8s/server*pem /opt/kubernetes/ssl/')
        with cd('/opt/kubernetes/ssl'):
            run('tar zcvf apiServer.tar ./*')
        # 备份远程生成api-server证书压缩包至本地
        get('/opt/kubernetes/ssl/apiServer.tar', 'backup/')

    @roles('node')
    @ignore(u'将证书传至node节点')
    def push_apiServer_node_cert(self):
        if not exists('/opt/kubernetes/apiServer.tar'):
            put('backup/apiServer.tar', '/opt/kubernetes/ssl')
            with cd('/opt/kubernetes/ssl'):
                run('tar zxf apiServer.tar')

    @roles('master')
    @ignore(u'生成kube-apiserver service文件')
    def create_apiserver_service(self):
        # 拼接etcd地址
        etcd_servers = ""
        for i in env.hosts:
            etcd_servers += f"https://{i}:2379,"

        # 读取模板文件
        with open('tools/apiServer/template/kube-apiserver.default', 'r') as f:
            tmp_data = ""
            for line in f.readlines():
                # format: 当前节点，etcd地址
                tmp_data += line.format(env.host, etcd_servers.rstrip(','))
            file = open('tmp/shell/create_service.sh', 'w')
            file.write(tmp_data)
            file.close()

        # 生成service
        exec_shell('tmp/shell', 'create_service.sh')

    @roles('master')
    @ignore(u'部署kube-apiserver')
    def deploy_apiserver(self):
        exec_shell('tools/apiServer', 'create_token.sh')
        run('systemctl daemon-reload')
        run('systemctl enable kube-apiserver')
        run('systemctl start kube-apiserver')
        run('systemctl status kube-apiserver')
        time.sleep(20)
        print(yellow('授权kubelet-bootstrap用户允许请求证书'))
        run(
            '/usr/bin/kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap')
        run(
            '/usr/bin/kubectl create clusterrolebinding kube-apiserver:kubelet-apis --clusterrole=system:kubelet-api-admin --user kubernetes')
        print(green('kube-apiserver部署完毕'))
