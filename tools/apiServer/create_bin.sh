#!/usr/bin/env bash
#########################################
# public methods
print_green () {
 echo -e "\033[32m$1 \033[0m"
}
print_red() {
 echo -e "\033[31m$1 \033[0m"
}
print_yellow() {
 echo -e "\033[33m$1 \033[0m"
}
# stty erase '^H'
#########################################

cd ~

mkdir -p /opt/kubernetes/{bin,cfg,ssl,logs}

if [ ! -d "/root/kubernetes" ]; then

    echo "文件不存在，下载文件"

    print_yellow "下载二进制文件..."

    wget http://10.0.86.24:8090/1.18/kubernetes-server-linux-amd64.tar.gz
    print_yellow "解压二进制包"

    tar zxvf kubernetes-server-linux-amd64.tar.gz

fi

path_pre="kubernetes/server/bin/"

cp ${path_pre}/kube-apiserver ${path_pre}/kube-scheduler ${path_pre}/kube-controller-manager ${path_pre}/kubelet ${path_pre}/kube-proxy /opt/kubernetes/bin

cp ${path_pre}/kubectl /usr/bin

print_yellow "验证复制文件正常"

ls /opt/kubernetes/bin