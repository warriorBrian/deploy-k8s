## deploy kubernetes

![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![macOS](https://img.shields.io/badge/macOS-passing-green)
![build](https://img.shields.io/badge/build-passing-green)
![python](https://img.shields.io/badge/python-3.7-blue)
![fabric](https://img.shields.io/badge/fabric-1.14-blue)

![#67C23A](https://placehold.it/15/67C23A/000000?text=+) Stability: 2 - **stable**

> kubernetes 1.18部署脚本，让部署变的更简单!

## 环境

> python >= 3.7

> Fabric3 == 1.14

> paramiko==2.7.1

> centos7/Debian

## 构建与运行 :rocket:

```bash
pip3 install
```

安装依赖项，运行:

```bash
python3 deploy.py
```

## 开始使用 :tada:

### 配置config.json:

> 配置项分为master, node两种角色

Example:

```json
{
      "host": "192.168.1.29",
      "password": "1",
      "hostname": "k8s-master",
      "user": "root",
      "port": 22
}
```
* host: 服务器IP地址
* password: 服务器密码
* hostname: **不可省略，不允许重复**
* user: SSH链接用户名
* port: SSH端口

:warning: 目前只支持单master进行部署(暂不支持多个master进行部署)，node角色中可为多个主机。
master唯一，只能存在一个，node存在若干个，判定方式为master必须存在，假设只存在一个master为单节点部署，如果存在node就为集群模式

### 配置address.json:

Example:

**`address.json`中的内容可为空，推荐搭建内网资源服务器，进行下载**
判断假设`address.json`中内容存在，则会覆盖默认下载地址。(如何搭建内网资源服务器，见下文)

```json
{
  "kubernetes_address": "",
  "cni_address": "",
  "flannel_address": "",
  "etcd_address": ""
}
```

### 开始部署:

确认`config.json`及`address.json`配置完毕，进行部署:

```bash
python3 deploy.py
```

## 目录结构

```
├── backup/                             备份文件目录
├── Controller/                         装饰器封装目录
│   ├── __init__.py
│   └── FabricController.py             装饰器及库引用
├── lib/                                模块化部署脚本目录
│   ├── ...
│   └── common.py                       公共引用文件
├── tmp/                                脚本生成临时文件目录
│   ├── hash/                           部署步骤，回滚记录(回滚对应步骤删除对应md5)
│   ├── shell/                          脚本自动生成临时sh文件及其他配置文件
│   └── logs/                           日志，记录执行步骤
├── tools/                              
│   ├── apiServer/                      部署kube-apiserver目录
│   │   ├── template/                   模板文件目录
│   │   ├── create_bin.sh               完成解压及基本工作
│   │   ├── create_service.sh           创建service脚本
│   │   └── create_token.sh             创建token脚本
│   ├── bin/                            cfssl证书生成工具等
│   ├── controller-manager/             部署kube-controller-manager目录
│   │   └── ...
│   ├── env/                            前置的环境准备脚本目录
│   ├── docker/                         部署docker目录
│   ├── etcd/                           部署etcd目录
│   ├── flanneld/                       部署flannel目录
│   ├── kube-proxy/                     部署kube-proxy目录
│   ├── kubelet/                        部署kubelet目录
│   └──  scheduler/                     部署kube-scheduler目录
├── address.json                        配置所需安装包下载地址
├── config.json                         配置kubernetes基本部署信息
├── deploy.py                           主入口，部署任务脚本
├── log.py                              生成日志脚本
└── requirements.txt                    依赖文件  
```

## 说明 :fire:

> 关于`tmp/hash`目录

在`tmp/logs`目录下，生成日志文件，按日期生成当进行部署时，会自动生成log记录:

Example:

```bash
2020-06-23 22:12:46,504 [INFO]- md5: 2d33ac1ea4571b6aa0cfb14746a8bbc1, Re-execute, delete this md5, dir: /hash
```

这个`md5`值会以目录形式在`tmp/hash`目录中创建，这是可靠的。(如果创建设备文件，在mac book上存在权限禁止创建问题)

当执行完某步骤，则下次以**同主机，同方法为判断依据，则不会执行，跳过该步骤。**

如果删除对应某个`md5`，则再次执行会执行对应步骤。

> 关于`hostname`设置

这是至关重要的，在部署kubernetes集群中，hostname应该是唯一的。

## 常见问题

> Q: 该如何搭建nginx资源服务器为k8s提供下载服务?

在服务器中安装`nginx`:

```bash
server {
 listen 8090;       # 监听端口
 server_name _;
 location / {
   root /data/k8s;  # 配置安装包目录地址
   index index.html index.htm;
   autoindex on;    # 开启目录浏览功能
 }
}
```
