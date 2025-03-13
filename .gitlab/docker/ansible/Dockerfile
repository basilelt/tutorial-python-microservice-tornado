FROM alpine/ansible:2.18.1

RUN apk add --no-cache python3 py3-kubernetes && \
    ansible-galaxy collection install kubernetes.core
