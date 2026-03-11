[![Testing](https://github.com/permia-cloud-security/sso-manager/actions/workflows/testing.yaml/badge.svg)](https://github.com/permia-cloud-security/sso-manager/actions/workflows/testing.yaml)
[![Linting](https://github.com/permia-cloud-security/sso-manager/actions/workflows/linting.yaml/badge.svg)](https://github.com/permia-cloud-security/sso-manager/actions/workflows/linting.yaml)
[![Python Security Scan (SAST)](https://github.com/permia-cloud-security/sso-manager/actions/workflows/scanning.yaml/badge.svg)](https://github.com/permia-cloud-security/sso-manager/actions/workflows/scanning.yaml)
[![codecov](https://codecov.io/github/islamelkadi/sso-entitlements-manager/graph/badge.svg?token=FFT650S5V5)](https://codecov.io/github/islamelkadi/sso-entitlements-manager)

# SSO Manager - Multi-Cloud Access Management Tool

> **Professional infrastructure-as-code access management for AWS, Azure, and Google Cloud Platform**

A modern CLI tool that transforms multi-cloud access control management using infrastructure-as-code patterns with plan/apply workflows. Built for enterprise environments requiring transparency, traceability, and automated access management across cloud platforms.

## 🚀 Quick Start

### Installation

#### Binary Download (Recommended)
Download the latest binary for your platform from the [releases page](https://github.com/permia-cloud-security/sso-manager/releases):

```bash
# Linux
curl -L https://github.com/permia-cloud-security/sso-manager/releases/latest/download/sso-manager-linux -o sso-manager
chmod +x sso-manager

# macOS
curl -L https://github.com/permia-cloud-security/sso-manager/releases/latest/download/sso-manager-macos -o sso-manager
chmod +x sso-manager

# Windows
# Download sso-manager-windows.exe from releases page
```

#### From Source
```bash
git clone https://github.com/permia-cloud-security/sso-manager.git
cd sso-manager
make build
```

### Usage

The tool follows infrastructure-as-code patterns with plan/apply commands:

```bash
# Show proposed access changes without executing them
sso-manager plan --manifest-path ./access-rules.yaml --log-level INFO

# Execute the proposed access changes
sso-manager apply --manifest-path ./access-rules.yaml --log-level INFO
```

### Environment Setup

Configure required environment variables:

```bash
export ROOT_OU_ID="r-xxxxxxxxxx"           # AWS Organizations Root OU ID
export IDENTITY_STORE_ID="d-xxxxxxxxxx"    # AWS Identity Center Store ID  
export IDENTITY_STORE_ARN="arn:aws:sso:::instance/ssoins-xxxxxxxxxx"  # Identity Center ARN
```

## 📋 Table of Contents

1. [Overview & Background](#overview--background)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [Development](#development)
6. [Roadmap](#roadmap)
7. [Contributing](#contributing)
8. [Professional Context](#professional-context)

## 🎯 Overview & Background

### The Multi-Cloud Access Challenge

In today's multi-cloud environment, organizations face significant challenges in managing access control at scale, particularly when implementing Single Sign-On (SSO) solutions. With numerous employees requiring access across AWS, Azure, and Google Cloud Platform through centralized authentication systems, the complexity of permission management has increased exponentially.

This challenge is particularly critical given the current threat landscape, where broken access control consistently ranks as the top security vulnerability in the OWASP Top 10. Many organizations rely on system administrators to create IAM roles and policies, granting access to users and groups typically synchronized from their SSO identity providers. However, this process, often executed through non-reproducible means such as manual console operations or CLI commands, lacks transparency and traceability, leaving organizations vulnerable to security risks and compliance issues.

### The Problem We Solve

Current multi-cloud access control management lacks the necessary transparency, traceability, and audibility. While SSO simplifies user authentication, organizations still struggle to answer fundamental questions about access provisioning within their cloud environments:

- **Who made access decisions and why?**
- **When were access provisions granted or revoked?**
- **How can we audit and track all access changes?**
- **Can we reproduce access configurations across environments?**

This lack of visibility, transparency, traceability and non-reproducibility, even in SSO-enabled environments, not only hampers effective security management but also exposes organizations to potential compliance violations and increased security risks, undermining some of the key benefits that SSO aims to provide.

### Our Solution: Infrastructure-as-Code for Access Management

SSO Manager transforms access control management from an opaque, manual process into a transparent, traceable, and automated system. Our git-based approach with centralized configuration offers:

1. **Infrastructure-as-Code**: Declarative YAML configuration for all access rules
2. **Plan/Apply Workflow**: Review changes before execution, similar to Terraform
3. **Git-Based Traceability**: Full version control and audit trails through commit history
4. **Multi-Cloud Ready**: Currently supports AWS, designed for Azure and GCP expansion
5. **Enterprise Integration**: Webhook support for existing workflows and project management systems
6. **Unified Control**: Single control panel for managing access across multiple cloud vendors
7. **Enhanced Transparency**: Commit messages and committer IDs provide clear insights into who made changes, when, and why
8. **Reproducibility**: Configuration-as-code approach makes all changes reproducible across environments
9. **Security Tool Integration**: Compatible with SIEM tools for enhanced security posture

This solution significantly reduces security risks and improves operational efficiency in multi-cloud environments while providing the audit trails crucial for compliance and security reviews.

### Related Work

Similar solutions addressing multi-cloud access management:

- [Manage permission sets and account assignments in AWS IAM Identity Center with a CI/CD pipeline](https://aws.amazon.com/blogs/infrastructure-and-automation/manage-permission-sets-and-account-assignments-in-aws-iam-identity-center-with-a-ci-cd-pipeline/)

## 🌟 Key Features

- **Plan/Apply Commands**: Infrastructure-as-code workflow for access management
- **Multi-Cloud Architecture**: Currently supports AWS, designed for Azure and GCP
- **Professional CLI**: Enterprise-grade command-line interface with comprehensive help
- **Binary Distribution**: Standalone executables for all major platforms
- **Automated Releases**: Semantic versioning with automated GitHub releases
- **Comprehensive Logging**: Configurable log levels for detailed execution tracking
- **Environment Integration**: Seamless integration with existing cloud environments

## 🏗️ Architecture

### Current Implementation (AWS)
```
Manifest File → SSO Manager → AWS Organizations → Identity Center Assignments
     ↓              ↓              ↓                    ↓
  YAML Rules    Plan/Apply    Account Mapping    Permission Sets
```

### Multi-Cloud Vision
```
                    ┌─── AWS Organizations ───┐
Manifest File ──→ SSO Manager ──┼─── Azure AD ──────────┼──→ Unified Access Control
                    └─── GCP IAM ─────────────┘
```

## ⚙️ Configuration

### Manifest File Structure

Create a YAML manifest file defining your access rules:

```yaml
rules:
  - rule_type: "allow"
    principal_type: "user"
    principal_name: "john.doe@company.com"
    permission_set_name: "ReadOnlyAccess"
    target_type: "account"
    target_name: "production-account"
    
  - rule_type: "allow"
    principal_type: "group"
    principal_name: "DevOps-Team"
    permission_set_name: "PowerUserAccess"
    target_type: "ou"
    target_name: "development-ou"
```

### Advanced Configuration

The tool supports complex access patterns:
- User and group-based assignments
- Account and Organizational Unit targeting
- Multiple permission set mappings
- Conditional access rules

## 🛠️ Development

### Prerequisites

- Python 3.13+
- Poetry for dependency management
- Docker for containerized development
- Make for build automation

### Development Setup

```bash
# Clone the repository
git clone https://github.com/permia-cloud-security/sso-manager.git
cd sso-manager

# Install development dependencies
make install-dev

# Start development environment
make dev-env

# Run tests
make unittest

# Format and lint code
make format

# Build binary
make build
```

### Build System

The project uses a modern Python build pipeline:
- **Poetry**: Python dependency management and packaging
- **PyInstaller**: Binary executable creation using `sso-manager.spec` configuration
- **python-semantic-release**: Automated GitHub releases and tagging
- **GitHub Actions**: Automated CI/CD pipeline

#### PyInstaller Configuration

The `sso-manager.spec` file is PyInstaller's configuration file that defines how to build the standalone executable:

```python
# sso-manager.spec - PyInstaller build configuration
a = Analysis(
    ['src/cli/sso.py'],           # Entry point script
    pathex=['.'],                 # Search paths
    datas=[                       # Include data files
        ('src/schemas/*.json', 'schemas'),
    ],
    hiddenimports=[               # Modules not auto-detected
        'boto3', 'botocore', 'yaml', 'jsonschema', 'rich'
    ],
    # ... other configuration
)
```

**What the .spec file does:**
- **Entry Point**: Specifies `src/cli/sso.py` as the main script
- **Dependencies**: Lists hidden imports that PyInstaller might miss
- **Data Files**: Includes JSON schema files needed at runtime
- **Build Options**: Configures single-file executable creation

This is the standard approach for PyInstaller - while not "pure Python," it's the industry-accepted method for creating standalone Python executables.

#### Simplified Version Management

The project uses a simplified approach to versioning:
- **CLI Version**: Points users to GitHub releases page for version information
- **GitHub Releases**: Automated releases with semantic versioning (v1.0.0, v1.1.0, etc.)
- **No Code Complexity**: No version parsing or complex version management in the codebase

### Testing

```bash
# Run unit tests with coverage
make unittest

# Run linting
make format

# Clean build artifacts
make clean-all
```

## 🗺️ Roadmap

### Phase 1: AWS Foundation ✅
- [x] AWS Organizations integration
- [x] Identity Center management
- [x] Plan/apply workflow
- [x] Binary distribution

### Phase 2: Multi-Cloud Expansion 🚧
- [ ] **Microsoft Azure Integration**
  - Azure Active Directory support
  - Azure subscription management
  - Role-based access control (RBAC)
  
- [ ] **Google Cloud Platform Integration**
  - GCP IAM integration
  - Project and organization management
  - Service account automation

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 Professional Context

This project showcases enterprise-grade software development practices:

- **Infrastructure-as-Code**: Modern DevOps patterns and workflows
- **Multi-Cloud Architecture**: Scalable design for cloud-native environments  
- **Professional CLI**: Enterprise-quality command-line interface
- **Automated Operations**: CI/CD, semantic releases, binary distribution
- **Security Focus**: Access control, audit trails, compliance readiness

Perfect for demonstrating skills in cloud security, DevOps automation, and enterprise software development.