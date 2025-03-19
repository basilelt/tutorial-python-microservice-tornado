# Python Microservice Tornado - CI/CD Pipeline Documentation

This document provides a comprehensive overview of the GitLab CI/CD pipeline for the Python Tornado microservice application.

## Table of Contents
- [Python Microservice Tornado - CI/CD Pipeline Documentation](#python-microservice-tornado---cicd-pipeline-documentation)
  - [Table of Contents](#table-of-contents)
  - [Pipeline Overview](#pipeline-overview)
    - [CI/CD Files Structure](#cicd-files-structure)
  - [Pipeline Stages](#pipeline-stages)
  - [Docker Images](#docker-images)
  - [Continuous Integration](#continuous-integration)
    - [Compliance Checks](#compliance-checks)
    - [Building Docker Images](#building-docker-images)
    - [Testing](#testing)
  - [Security Scanning](#security-scanning)
  - [Code Coverage](#code-coverage)
    - [Generation and Reporting](#generation-and-reporting)
    - [Coverage Deployment](#coverage-deployment)
  - [Continuous Deployment](#continuous-deployment)
    - [Deployment Types](#deployment-types)
  - [Application Testing](#application-testing)
  - [Kubernetes Configuration](#kubernetes-configuration)
    - [Namespace Management](#namespace-management)
    - [Kubernetes Resources](#kubernetes-resources)
  - [Environment Management](#environment-management)
    - [Review Environment Cleanup](#review-environment-cleanup)
    - [Environment URLs](#environment-urls)

## Pipeline Overview

The CI/CD pipeline automates the build, test, and deployment processes for the Python Tornado microservice. The pipeline is defined in `.gitlab/gitlab-ci.yml` and consists of multiple stages with jobs distributed across modular configuration files.

### CI/CD Files Structure

```
.gitlab/
├── ci/
│   ├── app-test.yml       # API endpoint testing jobs
│   ├── build.yml          # Docker image building jobs
│   ├── compliance.yml     # Linting and validation jobs
│   ├── coverage.yml       # Code coverage jobs
│   ├── deploy.yml         # Deployment jobs
│   └── test.yml           # Testing jobs
├── ansible/               # Ansible playbooks for Kubernetes deployment
├── docker/                # Dockerfiles for the application
└── scripts/               # Testing scripts
```

## Pipeline Stages

The pipeline consists of the following stages:

```
stages:
  - compliance
  - build
  - test
  - coverage
  - deploy
  - app-test
  - cleanup
```

1. **Compliance**: Validates Dockerfile and Ansible playbooks
2. **Build**: Builds Docker images using Kaniko
3. **Test**: Runs security scans, static type checking, linting, and unit tests
4. **Coverage**: Generates and displays code coverage reports
5. **Deploy**: Deploys the application to Kubernetes via Ansible
6. **App-Test**: Tests the deployed application's API endpoints
7. **Cleanup**: Cleans up resources when necessary

## Docker Images

The pipeline builds three distinct Docker images:

1. **Application Image**: Contains the Python microservice
   - `${CI_REGISTRY_IMAGE}:${TAG}`
   - Used for running the application

2. **Ansible Image**: Contains Ansible and Kubernetes tools
   - `${CI_REGISTRY_IMAGE}:ansible-${TAG}`
   - Used for deployment jobs

3. **Coverage Image**: Hosts the HTML code coverage report
   - `${CI_REGISTRY_IMAGE}:coverage-${TAG}`
   - Deployed alongside the main application

For tagged commits, images are tagged with the Git tag. For branch commits, images use the branch name as the tag.

## Continuous Integration

### Compliance Checks

The pipeline starts with validation checks:

- **docker-lint**: Uses Hadolint to validate all Dockerfiles
- **ansible-lint**: Validates Ansible playbooks for best practices

### Building Docker Images

Images are built using Kaniko, which doesn't require Docker-in-Docker privileges:

```yaml
build-image:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:v1.23.2-debug
    entrypoint: [""]
  # ...
  script:
    - /kaniko/executor
      --context "${CI_PROJECT_DIR}"
      --dockerfile "${CI_PROJECT_DIR}/.gitlab/docker/python/Dockerfile"
      --destination "${CI_REGISTRY_IMAGE}:${TAG}"
```

### Testing

Multiple test jobs run in parallel:

- **python-type-check**: Static type checking with MyPy
- **python-linter**: Code style checking with Flake8
- **python-unit-test**: Runs unit tests

## Security Scanning

Docker images are scanned for vulnerabilities using Trivy:

```yaml
docker-security-scan:
  stage: test
  image: 
    name: aquasec/trivy:0.60.0
    entrypoint: [""]
  # ...
  script:
    - trivy image "${CI_REGISTRY_IMAGE}:${TAG}" --no-progress --severity CRITICAL --exit-code 1
    - trivy image "${CI_REGISTRY_IMAGE}:${TAG}" --no-progress --severity HIGH --exit-code 0
```

The pipeline will fail if CRITICAL vulnerabilities are found, but only reports HIGH vulnerabilities without failing.

## Code Coverage

### Generation and Reporting

Code coverage reports are generated and converted to HTML:

```yaml
python-code-coverage:
  stage: coverage
  # ...
  script:
    - cd src
    - coverage run --source=addrservice --branch -m unittest discover tests -p '*_test.py'
    - coverage html
    - coverage report
```

### Coverage Deployment

Coverage reports are deployed to dedicated endpoints:

- Production: `http://coverage.${KUBE_DOMAIN}`
- Integration/Preproduction: `http://coverage.${CI_ENVIRONMENT_SLUG}.${KUBE_DOMAIN}`
- Review: `http://coverage.${CI_ENVIRONMENT_SLUG}.${KUBE_DOMAIN}`

## Continuous Deployment

Deployments are managed using Ansible playbooks that create Kubernetes resources:

### Deployment Types

1. **Production Deployment**
   - Triggered by Git tags
   - URL: `http://${KUBE_DOMAIN}`
   - 3 pod replicas for high availability

2. **Integration/Preproduction Deployment**
   - Triggered by specific branches
     - Integration: `develop` branch
     - Preproduction: `master` branch
   - URL: `http://${CI_ENVIRONMENT_SLUG}.${KUBE_DOMAIN}`
   - 1 pod replica

3. **Review Deployment**
   - Triggered by feature branches (branches starting with `feat-`)
   - URL: `http://${CI_ENVIRONMENT_SLUG}.${KUBE_DOMAIN}`
   - 1 pod replica
   - Includes cleanup job

```yaml
deploy_production:
  stage: deploy
  image: ${CI_REGISTRY_IMAGE}:ansible-${TAG}
  variables:
    TAG: $CI_COMMIT_TAG
  rules:
    - if: '$CI_COMMIT_TAG'
  # ...
```

## Application Testing

After deployment, the API endpoints are tested using a bash script:

```yaml
post-get-test:
  stage: app-test
  image: curlimages/curl:8.12.1
  # ...
  script:
    - sh .gitlab/scripts/api-test.sh $URL src/data/addresses/namo.json
    - sh .gitlab/scripts/api-test.sh $URL src/data/addresses/raga.json
```

The script tests the full CRUD cycle:
1. Creates an address entry using POST
2. Retrieves the entry using GET
3. Deletes the entry using DELETE
4. Verifies deletion with GET (expects 404)

## Kubernetes Configuration

### Namespace Management

Each environment gets its own Kubernetes namespace based on `CI_ENVIRONMENT_SLUG`. Namespaces are automatically created during deployment and can be cleaned up when environments are stopped.

### Kubernetes Resources

The Ansible playbooks create several Kubernetes resources:
- **Deployments**: Define pod configurations and replicas
- **Services**: Expose pods internally
- **Ingress**: Configure external access with custom hostnames
- **Secrets**: Store registry credentials and SSL certificates

For production environments:
```yaml
replicas: 3  # High availability with multiple replicas
```

For non-production environments:
```yaml
replicas: 1  # Single replica
```

## Environment Management

### Review Environment Cleanup

For review environments, the pipeline includes stop jobs to clean up resources:

```yaml
stop_review:
  stage: deploy
  # ...
  script:
    - cd .gitlab/ansible
    - ansible-playbook reset.yml --tags review
  environment:
    name: review/$TAG
    action: stop
  when: manual
```

### Environment URLs

The pipeline dynamically creates environment URLs:

- Production: `http://${KUBE_DOMAIN}`
- Non-production: `http://${CI_ENVIRONMENT_SLUG}.${KUBE_DOMAIN}`
- Coverage reports: `http://coverage.${CI_ENVIRONMENT_SLUG}.${KUBE_DOMAIN}`

---

This CI/CD pipeline ensures that code is thoroughly tested and securely deployed, with comprehensive coverage reporting and automated API testing to validate functionality at every stage.
