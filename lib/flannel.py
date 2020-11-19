from Controller.FabricController import *
from lib.common import exec_shell, clear_cache, unpack, download_address, status_message


class DeployFlanneld:
    def __init__(self):
        self.etcd_endpoints = ""
        for i in env.hosts:
            self.etcd_endpoints += f"https://{i}:2379,"

    def install(self):
        # pull flannel network plugins
        execute(self.pull_flannel_components)
        # create flanneld network information
        execute(self.configure_flannel_information)
        # create flanneld components service
        execute(self.create_flanneld_service)
        # deploy flanneld
        execute(self.deploy_flannel)
        # create rbac yaml
        execute(self.create_rbac)
        # update docker service
        execute(self.update_docker)

    @parallel
    @roles('master', 'node')
    @ignore(u'拉取flannel网络组件')
    def pull_flannel_components(self):
        if not exists('/opt/cni/bin'):
            print(yellow('创建CNI目录'))
            run('mkdir -p /opt/cni/bin')
        # CNI压缩包处理
        if not exists('/root/cni*.tgz'):
            run(f"wget {download_address['cni_address']}")
            print(yellow('解压CNI压缩包'))
            run('tar zxvf cni*.tgz -C /opt/cni/bin')
        else:
            print(yellow('解压CNI压缩包'))
            run('tar zxvf cni*.tgz -C /opt/cni/bin')
            print(blue(status_message['file_exist']))

        # flannel压缩包处理
        run(f"wget {download_address['flannel_address']}")
        run(f"tar zxf flannel*.tar.gz")
        run('cp /root/flanneld /root/mk-docker-opts.sh /usr/local/bin/')

    @roles('master')
    @ignore(u'配置flanneld网络信息')
    def configure_flannel_information(self):
        # 写入网段信息，网段与controller-manager网段保持一致
        # flanneld 不支持 etcd 3.4版本后的读写方式，两种方式:
        # 1. 将etcd降级为3.3.10,默认v2版本写入
        # 2. 将etcd以api v2版本启动，以v2版本写入网段信息 (这里采用这种)
        """
        ETCDCTL_API=2  ./etcdctl --ca-file=/opt/etcd/ssl/ca.pem \
          --cert-file=/opt/etcd/ssl/server.pem \
          --key-file=/opt/etcd/ssl/server-key.pem \
          --endpoints="https://${CLUSER_IP}:2379" \
          set /coreos.com/network/config  \
         '{ "Network": "10.244.0.0/16", "Backend": {"Type": "vxlan"}}'
        """
        print(yellow('向ETCD写入网段信息'))
        # 拼接写入etcd网段信息命令
        with open('tools/flanneld/template/network.config.default', 'r') as f:
            network_str = ""
            for i in f.readlines():
                network_str += i.format(self.etcd_endpoints.rstrip(","))
            file = open('tmp/shell/create_flanneld_network.sh', 'w')
            file.write(network_str)
            file.close()

        exec_shell('tmp/shell', 'create_flanneld_network.sh')

    @parallel
    @roles('master', 'node')
    @ignore(u'创建flanneld服务')
    def create_flanneld_service(self):
        template_data = ""
        with open('tools/flanneld/template/flanneld.config.default', 'r') as f:
            for i in f.readlines():
                template_data += i.format(self.etcd_endpoints.rstrip(","))
            file = open('tmp/shell/create_flanneld_service.sh', 'w')
            file.write(template_data)
            file.close()
        exec_shell('tmp/shell', 'create_flanneld_service.sh')

    @roles('master', 'node')
    @ignore('安装flanneld服务')
    def deploy_flannel(self):
        print(yellow('向系统注册flannel服务'))
        run('systemctl daemon-reload')
        run('systemctl enable flanneld')
        run('systemctl start flanneld')
        run('systemctl status flanneld')

    @roles('master')
    @ignore('授权访问kubelet')
    def create_rbac(self):
        put('tools/rbac/apiserver-to-kubelet-rbac.yaml', '/root')
        run('kubectl apply -f apiserver-to-kubelet-rbac.yaml')
        run('rm -rf /root/apiserver-to-kubelet-rbac.yaml')

    @roles('master', 'node')
    @ignore(u'指定docker子网段')
    def update_docker(self):
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

