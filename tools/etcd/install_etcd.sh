#!/usr/bin/env bash

bin_path='/opt/etcd/bin/'
file_list=("$bin_path/etcd" "$bin_path/etcdctl")
install_etcd () {
  echo "unzip the gz package"
  tar zxf etcd*.tar.gz
  rm -rf etcd*.tar.gz
  mv etcd* etcd

  if [ ! -f "$bin_path" ]; then
      mkdir -p "$bin_path"
  fi

  mv "etcd/etcd" "etcd/etcdctl" /opt/etcd/bin/

  echo "clean up useless folders"
  rm -rf etcd
}

# install if it does not exist
for file in "${file_list[@]}";do
  if [ ! -f "$file" ]; then
      install_etcd
  fi
done