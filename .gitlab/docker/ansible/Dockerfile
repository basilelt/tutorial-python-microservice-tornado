FROM alpine/ansible:2.18.1

RUN apk add --no-cache python3=3.12.9-r0 py3-kubernetes=31.0.0-r0 && \
    ansible-galaxy collection install kubernetes.core
