#!/usr/bin/env bash

# create dir
mkdir -p /usr/local/src/{ssh,kubernetes}
mkdir -p /var/lib/{kube-proxy,etcd,kubelet}
mkdir -p /opt/kubernetes/{ssl,logs,cfg,bin}
mkdir -p ~/TLS/{etcd,k8s}
mkdir -p /opt/etcd/{bin,cfg,ssl}
mkdir -p /etc/cni/net.d
mkdir -p /etc/docker

# close swap

sed -i '/swap/s/^/#/' /etc/fstab
swapoff -a
echo "执行回显结果论证"
free -m
sleep 1

# close selinux
if [[ $(getenforce) -eq 'Enforcing' ]];then
  setenforce 0
  sed -i 's/enforcing/disabled/' /etc/selinux/config
fi

# add kubernetes global path
echo "export PATH=/opt/kubernetes/bin/:$PATH" >> /etc/profile
source /etc/profile