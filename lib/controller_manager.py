from Controller.FabricController import *
from lib.common import exec_shell


# deploy kube controller manager

class DeployManager:
    def install(self):
        execute(self.deploy_manager)

    @roles('master')
    @ignore(u'部署kube-controller-manager')
    def deploy_manager(self):
        print(blue('部署kube-controller-manager'))
        exec_shell('tools/controller-manager', 'install_controller-manager.sh')
        print(green('kube-controller-manager部署完毕'))
