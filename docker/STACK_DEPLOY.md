# Deploy with Docker Swarm (secrets)

This document shows a minimal flow to deploy the project to Docker Swarm using secrets.

1) Initialize swarm on the server (once):

```bash
docker swarm init
```

2) Create secrets (interactive helper):

```bash
# will create service_auth_token and django_secret_key
./scripts/create_secrets.sh secrets
```

or manually:

```bash
printf '%s' "${SERVICE_AUTH_TOKEN}" | docker secret create service_auth_token -
printf '%s' "${SECRET_KEY}" | docker secret create django_secret_key -
```

3) Deploy the stack (uses `docker/docker-stack.yml`):

```bash
docker stack deploy -c docker/docker-stack.yml connectbot
```

4) Verify services and secrets:

```bash
docker service ls
docker secret ls
```

Notes
- Images should be built and pushed to a registry (example `alexom12/connectbot-web:latest`), or alternatively use `build:` in compose and deploy with docker-compose on a single host.
- Secrets are mounted at `/run/secrets/<name>` inside containers. The application reads secrets from those files if env vars are not set.
