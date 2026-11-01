# Dependency and release checks

CI runs Ruff, pytest, a runtime dependency audit and a container smoke test in mock mode. A failing check blocks the publish job. Third-party Actions are pinned to commit IDs. Review changes to those pins and dependency locks in pull requests.

The dependency audit currently fails on every reported vulnerability. Prefer upgrading; any future exception must document the advisory, impact, owner and expiration in a reviewed change. ECR scan-on-push findings require separate review: scan-on-push is not a deployment-blocking image scan.

Pull request jobs have read-only repository access and no AWS identity. Publishing is restricted to main, uses the release environment and AWS OIDC, and never uses stored AWS access keys. Release environment branch restrictions and the AWS trust subject both enforce that scope.
