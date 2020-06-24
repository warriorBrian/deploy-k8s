#!/usr/bin/env bash

# create token
createToken() {
echo "create token csv"
token=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' ')
echo "generate token: $token"
cat > /opt/kubernetes/cfg/token.csv << EOF
$token,kubelet-bootstrap,10001,"system:node-bootstrapper"
EOF
}

if [ ! -f "/opt/kubernetes/cfg/token.csv" ]; then
    createToken
fi