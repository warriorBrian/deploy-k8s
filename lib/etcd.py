from Controller.FabricController import *
from lib.common import exec_shell, download_address

cfssl_remote_path = ['/usr/local/bin/cfssl', '/usr/local/bin/cfssljson', '/usr/bin/cfssl-certinfo']
cfssl_local_path = ['tools/bin/cfssl_linux-amd64', 'tools/bin/cfssljson_linux-amd64', 'tools/bin/cfssl-certinfo_linux-amd64']


class DeployEtcd:
    def __init__(self):
        self.backup = f"{os.getcwd()}/backup"
        self.etcd_template = ""
        self.exists = True
        self.initial_cluster = ""

    def install(self):
        # configure the certificate file
        execute(self.configure_cert_file)
        # configure cert tools
        execute(self.configure_cert_tools)
        # generate cert files
        execute(self.generate_cert_file)
        # pull etcd components
        execute(self.pull_etcd_components)
        # configure etcd cluster
        execute(self.configure_etcd)
        # push etcd cert (node only)
        if env.roledefs['node']:
            execute(self.push_etcd_cert)
        # start etcd
        execute(self.deploy_etcd)

    # @parallel
    @roles('master')
    @ignore(u'配置生成证书所需文件项')
    def configure_cert_file(self):
        # 清空备份文件夹下所有文件，防止缓存文件冲突
        file_collections = os.listdir(self.backup)
        for file in file_collections:
            os.remove(f"{self.backup}/{file}")

        print(yellow('生成ETCD证书'))

        # 创建证书申请文件
        with open('tools/etcd/template/etcd-template.default', 'r') as f:
            for line in f.readlines():
                self.etcd_template += line.format(json.dumps(env.hosts))
        with open('tmp/shell/server-csr.json', 'w')as file:
            file.truncate()
            file.write(self.etcd_template)
            file.close()
        # 将证书申请文件传至各个节点
        put('tmp/shell/server-csr.json', '/root/TLS/etcd/')

    @roles('master')
    @ignore(u'配置证书生成工具')
    def configure_cert_tools(self):
        for i in cfssl_remote_path:
            if not os.path.exists(i):
                self.exists = False
        if not self.exists:
            for item in cfssl_local_path:
                put(item, '/root')
        else:
            print('程序已存在')

    @roles('master')
    @ignore(u'生成etcd证书')
    def generate_cert_file(self):
        # 上传并执行生成证书脚本
        exec_shell('tools/etcd', 'gencert.sh')
        # 备份远程生成etcd证书压缩包至本地
        get('/opt/etcd/ssl/etcd.tar.gz', 'backup/')
        get('/opt/etcd/etcd-all.tar.gz', 'backup/')

    @roles('master', 'node')
    @ignore(u'拉取etcd组件')
    def pull_etcd_components(self):
        run(f"wget {download_address['etcd_address']}")
        exec_shell('tools/etcd', 'install_etcd.sh')

    @roles('master', 'node')
    @ignore(u'生成etcd.conf配置文件')
    def configure_etcd(self):
        template_path = 'tools/etcd/template/etcd.config.default'
        # 读取config数据，取出所有配置拼接
        # 读取配置文件是否集群模式(is cluster?)
        # 根据配置生成模板 (generate templates based on config)
        for item in env.data:
            for i in env.data[item]:
                self.initial_cluster += f"{i['hostname']}=https://{i['host']}:2380,"

        # 读取模板文件，写入sh文件，生成etcd配置文件
        file_data = ""
        with open(template_path, 'r') as f:
            for line in f.readlines():
                # format: etcd name (only), etcd listen address, mailing address, cluster information
                file_data += line.format(env.hostname[env.host], '0.0.0.0', env.host, self.initial_cluster.rstrip(','))

        # 写入配置文件
        with open(f'tmp/shell/etcd.config-{env.hostname[env.host]}.sh', 'w') as f:
            f.write(file_data)
            f.close()
            self.initial_cluster = ''

        # 节点执行shell生成etcd.conf配置文件
        exec_shell('tmp/shell', f'etcd.config-{env.hostname[env.host]}.sh')

    @roles('node')
    @ignore(u'推送node节点证书，与master保持同步')
    def push_etcd_cert(self):
        if env.host:
            put('backup/etcd.tar.gz', '/opt/etcd/ssl')
            with cd('/opt/etcd/ssl'):
                run('tar zxvf etcd.tar.gz')
        else:
            print(yellow('不存在子节点，单master部署跳过推送证书'))

    @parallel
    @roles('master', 'node')
    @ignore(u'启动etcd')
    def deploy_etcd(self):
        run('systemctl daemon-reload')
        run('systemctl enable etcd')
        run('systemctl start etcd')
        run('systemctl status etcd')
        print(green('ETCD部署完毕'))
