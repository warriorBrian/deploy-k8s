from Controller.FabricController import *
from lib.common import status_message, exec_shell
'''
    配置所需环境，为安装kubernetes做准备
    required_components method:
        install: wget, docker, ntpdate
    requirement method:
        set the host,
        set the hostname
    
'''


class EnvConfigure:
    def __init__(self):
        tmp_path = f'{os.getcwd()}/tmp/shell'
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)

    def install(self):
        execute(self.requirement)
        execute(self.required_components)

    @roles('master', 'node')
    @ignore(u'安装必要组件')
    def required_components(self):
        wget_status = run('wget --version', quiet=True)
        if wget_status.failed:
            print(blue(status_message['wget_error_message']))
            put('tools/bin/wget-1.14-18.rpm', '/root')
            run('rpm -ivh /root/wget-1.14-18.rpm')
            run('rm -rf /root/wget*.rpm')

        docker_status = run('docker -v', quiet=True)
        if docker_status.failed:
            print(blue(status_message['docker_error_message']))
            put('tools/docker/docker*tgz', '/root')
            run('tar zxf docker*tgz')
            run('mv docker/* /usr/bin')
            print('上传docker service 文件')
            put('tools/docker/docker.service', '/usr/lib/systemd/system')
            docker_start_status = run('systemctl start docker')
            if docker_start_status.failed:
                print(red('docker启动失败，终止脚本，请手动排查'))
                exit(1)
            else:
                run('systemctl enable docker')
                run('systemctl status docker')
        # 时间同步
        print(blue('设置时间同步'))
        run('yum install ntpdate -y')
        run('timedatectl set-timezone Asia/Shanghai')
        run('ntpdate time.windows.com')

    @roles('master', 'node')
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

        with open('tmp/shell/hosts.sh', 'w') as template_env_host:
            template_env_host.write(template_host)
            template_env_host.close()

        exec_shell('tmp/shell', 'hosts.sh')

        print(blue('关闭firewalld'))

        run('systemctl stop firewalld')
        run('systemctl disable firewalld')

        self.set_hostname()
        exec_shell('tools/env', 'env.sh')
        print(blue('执行重启，请勿操作...'))
        reboot()

    @ignore(u'设置主机名')
    def set_hostname(self):
        run(f"hostnamectl set-hostname {env.hostname[env.host]}")
        host_name = run('hostname')
        print(blue(f"hostname: {host_name}"))
        time.sleep(1)

    @roles('master', 'node')
    @ignore(u'创建所需文件夹')
    def create_folder(self):
        run('mkdir -p ~/TLS/{etcd,k8s}')
        run('mkdir -p /opt/etcd/{bin,cfg,ssl}')
        run('mkdir -p /opt/kubernetes/{bin,cfg,ssl,logs}')

