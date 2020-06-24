#!/usr/bin/env bash
##############################
# Stand-alone mode
##############################
cfg_dir="/opt/kubernetes/cfg"

if [ ! -d "$cfg_dir" ];then
    mkdir -p "$cfg_dir"
fi

cat > /opt/etcd/cfg/etcd.conf << EOF
#[Member]
ETCD_NAME="k8s-master"
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
ETCD_LISTEN_PEER_URLS="https://192.168.1.29:2380"
ETCD_LISTEN_CLIENT_URLS="https://192.168.1.29:2379"
#[Clustering]
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.1.29:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.1.29:2379"
ETCD_INITIAL_CLUSTER="k8s-master=https://192.168.1.29:2380,k8s-node1=https://192.168.1.33:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="new"
EOF

# 创建etcd service文件
cat > /usr/lib/systemd/system/etcd.service << EOF
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target
[Service]
Type=notify
EnvironmentFile=/opt/etcd/cfg/etcd.conf
ExecStart=/opt/etcd/bin/etcd \
--cert-file=/opt/etcd/ssl/server.pem \
--key-file=/opt/etcd/ssl/server-key.pem \
--peer-cert-file=/opt/etcd/ssl/server.pem \
--peer-key-file=/opt/etcd/ssl/server-key.pem \
--trusted-ca-file=/opt/etcd/ssl/ca.pem \
--peer-trusted-ca-file=/opt/etcd/ssl/ca.pem \
--logger=zap \
--enable-v2=true
Restart=on-failure
LimitNOFILE=65536
[Install]
WantedBy=multi-user.target
EOF