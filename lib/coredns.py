from Controller.FabricController import *


class DeployCoreDns:
    def __init__(self):
        pass

    def install(self):
        # apply coredns
        execute(self.apply_coredns)
        # install conntrack-tools
        execute(self.install_conntrack)
        # restart kube-proxy kubelet
        execute(self.restart_components)
        # announce message
        execute(self.announce_message)

    @roles('master')
    @ignore(u'配置coredns')
    def apply_coredns(self):
        if not exists('/root/coredns.yaml'):
            put('tools/coredns/coredns.yaml', '/root')
        run('kubectl apply -f /root/coredns.yaml')

    @roles('master', 'node')
    @ignore(u'安装conntrack-tools组件')
    def install_conntrack(self):
        conntrack_status = run('conntrack --version', quiet=True)
        if conntrack_status.failed:
            print(blue('conntrack-tools不存在，执行安装'))
            put('tools/bin/libnetfilter_cthelper*.rpm', '/root')
            put('tools/bin/libnetfilter_cttimeout*.rpm', '/root')
            put('tools/bin/libnetfilter_queue*.rpm', '/root')
            put('tools/bin/conntrack*.rpm', '/root')
            run('rpm -ivh /root/libnetfilter_cthelper*.rpm')
            run('rpm -ivh /root/libnetfilter_cttimeout*.rpm')
            run('rpm -ivh /root/libnetfilter_queue*.rpm')
            run('rpm -ivh /root/conntrack*.rpm')
        else:
            print(blue('conntrack-tools存在，跳过安装'))

    @parallel
    @roles('master', 'node')
    @ignore(u'重启kube-proxy及kubelet组件')
    def restart_components(self):
        run('systemctl restart kube-proxy')
        run('systemctl restart kubelet')

    @roles('master', 'node')
    def announce_message(self):
        print(green(f"IP:{env.host}, host: {env.hostname[env.host]}, 部署完毕!"))
