# Next session: understand the local workload

1. Run the tests and the application. Explain image vs container, port mapping, health vs readiness, and why weather fixtures are labeled.
2. Request Atlanta, an unknown city, Springfield and an empty city. Explain each status code.
3. Inspect JSON logs and `/metrics`. Explain why city names and request IDs are not metric labels.
4. Build and smoke-test Docker. Record the image ID and resolved base digest.
5. Create a Git repository and review the files before the first commit. Keep credentials and virtual environments out of Git.
6. Begin the separate `weather-status-platform` repository: kind cluster, namespace, Deployment, ClusterIP Service, ConfigMap, probes, resource limits and two replicas.
7. Diagnose a bad image, incorrect Service target port and failed readiness probe. Record actual commands and recovery evidence.

Then add GitHub Actions and Argo CD locally before EKS. Choose a live weather provider only after reviewing terms, authentication and quotas. Keep CI and load tests offline. Never add a fake secret unless clearly labeled as a secrets-integration exercise.
