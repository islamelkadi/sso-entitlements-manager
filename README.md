<!-- Pytest Coverage Comment:Begin -->
<!-- Pytest Coverage Comment:End -->

[![Testing](https://github.com/permia-cloud-security/sso-manager/actions/workflows/testing.yaml/badge.svg)](https://github.com/permia-cloud-security/sso-manager/actions/workflows/testing.yaml)

[![Linting](https://github.com/permia-cloud-security/sso-manager/actions/workflows/linting.yaml/badge.svg)](https://github.com/permia-cloud-security/sso-manager/actions/workflows/linting.yaml)

[![Scanning](https://github.com/permia-cloud-security/sso-manager/actions/workflows/scanning.yaml/badge.svg)](https://github.com/permia-cloud-security/sso-manager/actions/workflows/scanning.yaml)

# Design Document

## 1. *Introduction*

### 1.1 *Background*
In today's multi-cloud environment, organizations face significant challenges in managing access control at scale, particularly when implementing Single Sign-On (SSO) solutions. With numerous employees requiring access across various cloud vendors through a centralized authentication system, the complexity of permission management has increased exponentially. This challenge is particularly critical given the current threat landscape, where broken access control consistently ranks as the top security vulnerability in the OWASP Top 10. Many organizations rely on system administrators to create IAM roles and policies, granting access to users and groups typically synchronized from their SSO identity providers. However, this process, often executed through non-reproducible means such as manual console operations or CLI commands, lacks transparency and traceability, leaving organizations vulnerable to security risks and compliance issues, despite the enhanced security that SSO provides.

### 1.2 *Problem Statement*
The current approach to managing multi-cloud access control through SSO lacks the necessary transparency, traceability, and audibility. While SSO simplifies user authentication, organizations still struggle to answer fundamental questions about access provisioning within their cloud environments, including the rationale behind access decisions, the individuals responsible for granting access, and the timing of access provisions. This lack of visibility, transparency, traceability and non-reproducibility, even in SSO-enabled environments, not only hampers effective security management but also exposes organizations to potential compliance violations and increased security risks, undermining some of the key benefits that SSO aims to provide.

### 1.3 *Proposed Solution*
To address the challenges of traceability, transparency, and reproducibility in multi-cloud access control management, we propose a git-based approach with a centralized configuration file. This solution offers:

1. **Unified Control*: A single control panel for managing access across multiple cloud vendors, streamlining the process and reducing complexity.
2. **Version Control*: Leveraging git's native capabilities to provide full traceability of changes through commit history, ensuring every modification is logged and reversible.
3. **Enhanced Transparency*: Commit messages and committer IDs offer clear insights into who made changes, when they were made, and why, addressing the current lack of context in access provisioning.
4. **Process Integration*: Capability to integrate with existing workflows through webhooks, enabling ties to project management systems and ensuring changes are associated with approved tickets.
5. **Auditability*: The git-based system creates an auditable trail of all access control modifications, crucial for compliance and security reviews.
6. **Reproducibility*: By moving from manual processes to a configuration-as-code approach, all changes become reproducible and can be easily applied across environments.
7. **Security Tool Integration**: Compatibility with security information and event management (SIEM) tools, enhancing overall security posture and incident response capabilities.

This solution transforms access control management from an opaque, manual process into a transparent, traceable, and automated system, significantly reducing security risks and improving operational efficiency in multi-cloud environments.

### 1.4 *Related Work*
The following is a list of similar solutions that have been created to address this issue:

- [Manage permission sets and account assignments in AWS IAM Identity Center with a CI/CD pipeline](https://aws.amazon.com/blogs/infrastructure-and-automation/manage-permission-sets-and-account-assignments-in-aws-iam-identity-center-with-a-ci-cd-pipeline/)
