from Controller.FabricController import *
from lib.common import exec_shell, unpack, approve_cert


class DeployKubelet:
    def __init__(self):
        for i in env.data['master']:
            self.master_host = i['host']

    def install(self):
        # create kubelet service files
        execute(self.create_kubelet_service)
        # node kubelet deploy
        # approve cert
        if env.roledefs['node']:
            execute(self.create_node_kubelet)
            execute(self.approve_kubelet_cert)

    @roles('master', 'node')
    @ignore(u'创建kubelet service')
    def create_kubelet_service(self):
        if not exists('/opt/kubernetes/cfg/kubelet-config.yml'):
            put('tools/kubelet/template/kubelet-config.yml', '/opt/kubernetes/cfg')
        template_data = ""
        with open('tools/kubelet/template/create_kubelet_config.default', 'r') as f:
            for line in f.readlines():
                template_data += line.format(f"{env.host}", self.master_host)
            file = open(f'tmp/shell/create_kubelet_service_{env.hostname[env.host]}.sh', 'w')
            file.write(template_data)
            file.close()
            print(f"{env.host}: 写入文件完成")

        if env.host in env.roledefs['master']:
            # 打包cfg文件, master
            unpack('/opt/kubernetes/cfg/', 'kubernetes-token.tar.gz', 'token.csv --exclude kubelet-client*')
            exec_shell('tmp/shell', f'create_kubelet_service_{env.hostname[env.host]}.sh')
            approve_cert()
        else:
            # node
            print('node节点上传token.csv文件')
            put('backup/kubernetes-token.tar.gz', '/root')
            run('tar zxvf kubernetes-token.tar.gz -C /opt/kubernetes/cfg/')

    @roles('node')
    @ignore(u'创建node节点kubelet service')
    def create_node_kubelet(self):
        exec_shell('tmp/shell', f'create_kubelet_service_{env.hostname[env.host]}.sh')

    @roles('master')
    @ignore(u'批准kubelet证书申请')
    def approve_kubelet_cert(self):
        approve_cert()
