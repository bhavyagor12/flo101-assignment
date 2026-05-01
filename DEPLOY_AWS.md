# Deploy to a Single AWS EC2 Instance

This is the simplest production-shaped deployment for the assessment demo:

- one EC2 instance
- Docker Compose
- web exposed publicly on port 80
- API reachable only inside Docker, through the web container's `/api` proxy
- SQLite and uploaded corpora persisted in Docker named volumes

## 1. Create the EC2 Instance

Recommended starting point:

- AMI: Ubuntu Server 24.04 LTS
- Instance type: `t3.small` minimum, `t3.medium` preferred
- Storage: 20 GB gp3
- Security group inbound rules:
  - SSH: TCP 22 from your IP only
  - HTTP: TCP 80 from `0.0.0.0/0`

If you set `WEB_PORT=3000`, open TCP 3000 instead of TCP 80.

## 2. Bootstrap the Instance

SSH into the instance, clone or copy this repo, then run:

```bash
sudo bash scripts/bootstrap-ec2-ubuntu.sh
```

If the script adds your user to the Docker group, log out and back in.

## 3. Configure Secrets

```bash
cp .env.aws.example .env
nano .env
```

Fill at least:

- `OPENROUTER_API_KEY` — used for both chat completions and embeddings.

Keep `VITE_API_BASE_URL=/api` for the EC2 setup. Browser requests hit the
same host, and the web container proxies `/api` to the API container.

## 4. Deploy

```bash
./scripts/deploy-aws.sh
```

Open:

```text
http://<EC2_PUBLIC_IP>
```

## 5. Operate

View logs:

```bash
docker compose -f docker-compose.aws.yml logs -f
```

Restart:

```bash
docker compose -f docker-compose.aws.yml restart
```

Rebuild after pulling code changes:

```bash
git pull
./scripts/deploy-aws.sh
```

Stop:

```bash
docker compose -f docker-compose.aws.yml down
```

Delete app data:

```bash
docker compose -f docker-compose.aws.yml down -v
```

The `-v` form deletes SQLite evaluations and uploaded corpus data.

## Notes

- This deployment is appropriate for a demo or assessment review.
- For a long-lived public deployment, put an AWS Application Load Balancer or
  Caddy/Nginx with TLS in front of the web container.
- The API container is intentionally not exposed to the public internet. All
  browser API traffic goes through the web container's `/api` reverse proxy.
