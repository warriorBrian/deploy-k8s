#!/usr/bin/env bash

etcd_version="v3.4.9"
etcd_path="etcd-$etcd_version-linux-amd64"
bin_path='/opt/etcd/bin/'
file_list=("$bin_path/etcd" "$bin_path/etcdctl")
install_etcd () {
  # 从本地上传，防止拉取超时
  #  echo "pull etcd from the network"
  #  wget "http://github.com/coreos/etcd/releases/download/$etcd_version/etcd-$etcd_version-linux-amd64.tar.gz"
  echo "unzip the gz package"
  tar zxf "etcd-$etcd_version-linux-amd64.tar.gz"

  if [ ! -f "$bin_path" ]; then
      mkdir -p "$bin_path"
  fi

  mv "$etcd_path/etcd" "$etcd_path/etcdctl" /opt/etcd/bin/

  echo "clean up useless folders"
  rm -rf etcd-${etcd_version}*
}

# install if it does not exist
for file in "${file_list[@]}";do
  if [ ! -f "$file" ]; then
      install_etcd
  fi
done