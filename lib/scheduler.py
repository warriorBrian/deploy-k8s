from Controller.FabricController import *
from lib.common import exec_shell


# deploy kube-scheduler

class DeployScheduler:
    def install(self):
        execute(self.deploy_scheduler)

    @roles('master')
    @ignore(u'部署kube-scheduler')
    def deploy_scheduler(self):
        print(blue('部署kube-scheduler'))
        exec_shell('tools/scheduler', 'install_scheduler.sh')
        print(green('kube-scheduler部署完毕'))
