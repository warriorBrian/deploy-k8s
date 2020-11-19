from Controller.FabricController import *
from lib.common import exec_shell, clear_cache, unpack


class DeployProxy:
    def __init__(self):
        pass

    def install(self):
        # create kube-proxy config files
        execute(self.create_proxy_config)
        if env.roledefs['node']:
            execute(self.push_node_proxy_config)
        # deploy kube-proxy
        execute(self.deploy_proxy)

    @roles('master')
    @ignore(u'创建kube-proxy配置')
    def create_proxy_config(self):
        # 清理备份文件
        clear_cache('kube-proxy.tar.gz')
        with open('tools/kube-proxy/template/kube-proxy-config.default', 'r') as f:
            template_data = ""
            for line in f.readlines():
                template_data += line.format(f"{env.host}", env.host)
            file = open('tmp/shell/create_kube-proxy_config.sh', 'w')
            file.write(template_data)
            file.close()

        # 上传文件
        put('tools/kube-proxy/template/kube-proxy.conf', '/opt/kubernetes/cfg')
        put('tools/kube-proxy/template/kube-proxy-csr.json', '/root/TLS/k8s')

        # 签发证书
        with cd('/root/TLS/k8s'):
            run('cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes kube-proxy-csr.json | cfssljson -bare kube-proxy')
            run('ls kube-proxy*pem')
            run('tar zcvf kube-proxy.tar.gz kube-proxy*pem')
            get('/root/TLS/k8s/kube-proxy.tar.gz', 'backup/')

        # 执行生成脚本，生成配置文件及kube-proxy配置文件等
        exec_shell('tmp/shell', 'create_kube-proxy_config.sh')
        # 拷贝生成配置文件到指定目录
        run('cp /root/kube-proxy.kubeconfig /opt/kubernetes/cfg/')
        # 上传kube-proxy service文件
        put('tools/kube-proxy/template/kube-proxy.service', '/usr/lib/systemd/system')
        # 打包kube-proxy文件
        unpack('/opt/kubernetes/cfg/', 'kubernetes-proxy.tar.gz', './kube-proxy.kubeconfig ./kube-proxy-config.yml')

    @roles('node')
    @ignore(u'推送node节点kube-proxy配置文件')
    def push_node_proxy_config(self):
        put('tools/kube-proxy/template/kube-proxy.conf', '/opt/kubernetes/cfg')
        put('backup/kubernetes-proxy.tar.gz', '/root')
        run('tar zxvf kubernetes-proxy.tar.gz -C /opt/kubernetes/cfg/')
        put('tools/kube-proxy/template/kube-proxy.service', '/usr/lib/systemd/system')

    @roles('master', 'node')
    @ignore(u'部署节点kube-proxy')
    def deploy_proxy(self):
        # 开启服务
        run('systemctl daemon-reload')
        run('systemctl stop kube-proxy')
        run('systemctl start kube-proxy')
        run('systemctl enable kube-proxy')
        run('systemctl status kube-proxy')
        print(green(f'{env.hostname[env.host]}: kube-proxy部署完毕'))
