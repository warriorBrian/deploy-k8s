from lib.env import EnvConfigure
from lib.etcd import DeployEtcd
from lib.api_server import DeployApiServer
from lib.controller_manager import DeployManager
from lib.scheduler import DeployScheduler
from lib.kubelet import DeployKubelet
from lib.proxy import DeployProxy
from lib.flannel import DeployFlanneld


class Deploy:
    def __init__(self):
        # env configure
        env_config = EnvConfigure()
        env_config.install()

        # etcd install
        deploy_etcd = DeployEtcd()
        deploy_etcd.install()

        # kube-apiserver install
        deploy_api_server = DeployApiServer()
        deploy_api_server.install()

        # deploy kube-controller-manager
        deploy_manager = DeployManager()
        deploy_manager.install()

        # deploy kube-scheduler
        deploy_scheduler = DeployScheduler()
        deploy_scheduler.install()

        # deploy kubelet
        deploy_kubelet = DeployKubelet()
        deploy_kubelet.install()

        # deploy kube-proxy
        deploy_proxy = DeployProxy()
        deploy_proxy.install()

        # deploy flanneld
        deploy_flanneld = DeployFlanneld()
        deploy_flanneld.install()


if __name__ == '__main__':
    Deploy()
