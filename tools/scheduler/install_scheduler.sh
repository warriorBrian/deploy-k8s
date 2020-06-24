#!/usr/bin/env bash
service_path="/etc/systemd/system"
service_name="kube-scheduler.service"
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
createSchedulerFile() {

print_yellow "生成scheduler配置文件"

cat > /opt/kubernetes/cfg/kube-scheduler.conf << EOF
KUBE_SCHEDULER_OPTS="--logtostderr=false \
--v=2 \
--log-dir=/opt/kubernetes/logs \
--leader-elect \
--master=127.0.0.1:8080 \
--bind-address=127.0.0.1"
EOF

print_yellow "创建service文件"

cat > /usr/lib/systemd/system/kube-scheduler.service << EOF
[Unit]
Description=Kubernetes Scheduler
Documentation=https://github.com/kubernetes/kubernetes
[Service]
EnvironmentFile=/opt/kubernetes/cfg/kube-scheduler.conf
ExecStart=/opt/kubernetes/bin/kube-scheduler \$KUBE_SCHEDULER_OPTS
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF

}

if [ ! -f "$service_path/$service_name" ]; then
    echo "file does not exist, create scheduler service"
    createSchedulerFile
else
    echo "file exists, skip creation!"
fi

systemctl daemon-reload
systemctl enable kube-scheduler
systemctl start kube-scheduler
systemctl status kube-scheduler