# AI-Powered Code Review Kubernetes Operator

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Go Report Card](https://goreportcard.com/badge/github.com/yourusername/code-review-operator)](https://goreportcard.com/report/github.com/yourusername/code-review-operator)

A Kubernetes operator that automates code reviews using Large Language Models. This operator integrates with your existing CI/CD pipelines to provide intelligent, automated code feedback, reducing bugs and improving code quality without manual intervention.

## 🚀 Features

- **Automated Code Reviews**: Integrates with GitHub, GitLab, and Bitbucket to automatically review pull requests
- **Multi-Model Support**: Connect to OpenAI, Anthropic, or open-source LLMs
- **Customizable Rules**: Define organization-specific coding standards and policies
- **Language Awareness**: Specialized handling for different programming languages
- **Cost Optimization**: Token usage management and caching to reduce API costs
- **Review Analytics**: Track the impact and quality of AI-powered reviews
- **Kubernetes Native**: Fully integrated with Kubernetes using custom resources
- **Scalable Architecture**: Handles code reviews for organizations of any size

## 🛠️ Architecture

![Architecture Diagram](docs/images/architecture.png)

The operator consists of:

1. **Controller**: Manages the lifecycle of code review requests
2. **Git Connector**: Interacts with Git providers to fetch and post comments
3. **LLM Service**: Manages interactions with AI models
4. **Review Engine**: Processes code diffs and generates meaningful feedback
5. **Policy Engine**: Enforces organization-specific rules and standards
6. **Analytics Service**: Tracks metrics and provides insights

## 📋 Prerequisites

- Kubernetes cluster (v1.18+)
- kubectl
- Go 1.20+ (for development)
- Access to at least one LLM provider (OpenAI, Anthropic, etc.)
- Access to Git repository APIs (GitHub, GitLab, etc.)

## 🔧 Installation

### Using Helm

```bash
helm repo add code-review-operator https://yourusername.github.io/code-review-operator/charts
helm repo update
helm install code-review-operator code-review-operator/code-review-operator \
  --namespace code-review-system \
  --create-namespace \
  --set config.llmProvider=openai \
  --set config.gitProvider=github \
  --set secrets.llmApiKey=<your-api-key> \
  --set secrets.gitToken=<your-git-token>
```

### Using kubectl

```bash
# Install CRDs
kubectl apply -f https://raw.githubusercontent.com/yourusername/code-review-operator/main/config/crd/bases/code-review.io_codereviewrequests.yaml
kubectl apply -f https://raw.githubusercontent.com/yourusername/code-review-operator/main/config/crd/bases/code-review.io_codereviewconfigs.yaml

# Create namespace
kubectl create namespace code-review-system

# Create secrets
kubectl create secret generic llm-credentials \
  --namespace code-review-system \
  --from-literal=api-key=<your-api-key>

kubectl create secret generic git-credentials \
  --namespace code-review-system \
  --from-literal=token=<your-git-token>

# Deploy operator
kubectl apply -f https://raw.githubusercontent.com/yourusername/code-review-operator/main/config/deployment/deployment.yaml
```

## 🔍 Usage

### Creating a Code Review Configuration

```yaml
apiVersion: code-review.io/v1alpha1
kind: CodeReviewConfig
metadata:
  name: default-review-config
  namespace: code-review-system
spec:
  gitProvider:
    type: github
    organization: your-org
    repositories:
      - name: your-repo
        branches:
          - main
          - dev
  llmConfig:
    provider: openai
    model: gpt-4
    maxTokens: 8192
  reviewPolicy:
    severity:
      critical: true
      major: true
      minor: true
      suggestion: true
    rules:
      - name: security-check
        enabled: true
      - name: performance-check
        enabled: true
  notifications:
    slack:
      enabled: true
      channel: "#code-reviews"
```

### Manually Triggering a Review

```yaml
apiVersion: code-review.io/v1alpha1
kind: CodeReviewRequest
metadata:
  name: manual-review-request
  namespace: code-review-system
spec:
  repository: your-org/your-repo
  pullRequest: 123
  config: default-review-config
```

## 📊 Dashboard

Access the dashboard by port-forwarding to the operator's service:

```bash
kubectl port-forward -n code-review-system svc/code-review-dashboard 8080:80
```

Then open http://localhost:8080 in your browser.

## 📖 Documentation

Full documentation is available at [docs/](docs/README.md)

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [API Reference](docs/api.md)
- [Language Support](docs/languages.md)
- [Troubleshooting](docs/troubleshooting.md)

## 💻 Development

### Prerequisites

- Go 1.20+
- Docker
- Kubernetes cluster (minikube, kind, or remote)
- Operator SDK

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/code-review-operator.git
cd code-review-operator

# Install dependencies
go mod download

# Build the operator
make build

# Run locally
make run
```

### Testing

```bash
# Run unit tests
make test

# Run integration tests
make test-integration
```

## 🤝 Contributing

Contributions are welcome! Please check out our [Contributing Guide](CONTRIBUTING.md).

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Acknowledgments

- The Kubernetes Operator Framework team
- The Go community
- All contributors to this project
