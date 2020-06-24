#!/bin/sh
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

# 配置证书生成工具
chmod +x cfssl*
mv cfssl_linux-amd64 /usr/local/bin/cfssl
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
mv cfssl-certinfo_linux-amd64 /usr/bin/cfssl-certinfo

mkdir -p ~/TLS/{etcd,k8s}

cd ~/TLS/etcd

cat > ~/TLS/etcd/ca-config.json << EOF
{
  "signing": {
    "default": {
      "expiry": "87600h"
    },
    "profiles": {
      "www": {
         "expiry": "87600h",
         "usages": [
            "signing",
            "key encipherment",
            "server auth",
            "client auth"
        ]
      }
    }
  }
}
EOF

# CN common Name C: country L: Locality O: 组织名称 OU: 组织单位名称 ST: 州， 省
cat > ~/TLS/etcd/ca-csr.json << EOF
{
    "CN": "etcd CA",
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "L": "Beijing",
            "ST": "Beijing"
        }
    ]
}
EOF

# 生成CA证书和CA私钥及CSR(证书签名请求)
# 生成运行CA所必需的文件ca-key.pem（私钥）和ca.pem（证书），还会生成ca.csr（证书签名请求），用于交叉签名或重新签名
cfssl gencert -initca ~/TLS/etcd/ca-csr.json | cfssljson -bare ca -

sleep 2

echo "list all CA certificates"

print_yellow "生成server证书"

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=www server-csr.json | cfssljson -bare server

sleep 2

print_yellow "备份证书"

mkdir -p /opt/etcd/{bin,cfg,ssl}

cp ~/TLS/etcd/ca*pem ~/TLS/etcd/server*pem /opt/etcd/ssl/

# 进入目录备份文件
cd /opt/etcd/ssl/

tar zcvf etcd.tar.gz ./*

cd /opt/etcd

tar zcvf etcd-all.tar.gz ssl/

#退出目录
cd ~