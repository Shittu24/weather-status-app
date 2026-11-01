# CirrusLabs role alignment

Based on the job description supplied by the user on October 31, 2026. This is a portfolio lab, not employment experience. A project can demonstrate skills but does not replace the listed 1-2 years of experience.

| Role requirement | Project implementation/evidence target | Current state |
|---|---|---|
| Docker, scripting, troubleshooting | Non-root image, smoke script, provider failure tests | Local foundation implemented; see evidence log for verification |
| Kubernetes / EKS | Local kind lab first, then EKS; pods, Deployment, Service, probes and namespace | Planned |
| GitHub Actions CI | PR lint/test/build; main publishes a digest to ECR through scoped OIDC | Planned |
| Argo CD / GitOps | Separate platform repository, reviewed image-digest changes, Git revert recovery | Planned |
| Terraform / AWS | Separate backend bootstrap and dev roots, VPC, private workers, EKS and IAM | Planned |
| Doppler or similar secrets solution | AWS Secrets Manager with EKS Pod Identity; denied-access and rotation evidence | Planned |
| JFrog or similar artifact repository | ECR for OCI images, immutable release identity, lifecycle policy | Planned; ECR does not demonstrate JFrog package administration |
| Git workflows and collaboration | Feature branch, reviewable PR, CI failure and corrected change | Planned |
| Linux and troubleshooting | Container logs, pod events, wrong-port and bad-image drills | Planned |
| Helm, monitoring and logging | Prometheus/Grafana lab, CloudWatch logs, pinned chart versions | App instrumentation implemented; platform planned |

Prioritize these requirements before advanced SQS/KEDA/canary extensions. AWS Secrets Manager and ECR address the role's allowance for similar tools; do not claim Doppler or JFrog hands-on experience without using them.

Application-ready demonstration: test failure blocks a release; passing build publishes an immutable artifact; approved Git change deploys to EKS; Argo CD reconciles; monitoring reveals an injected issue; Git revert restores service. Save CI links, commit IDs, image digests and measured recovery results.

Before provisioning AWS, choose the region and spending ceiling, estimate current costs, configure budget alerts, review the Terraform plan and document teardown. No AWS resources are provisioned in this milestone.
