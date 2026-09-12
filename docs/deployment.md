# Deployment to Google Cloud Run

**Status:** Production-only system. Single environment.  
**Last updated:** 2026-09-12

---

## Pre-deployment checklist

1. **Full test suite passes locally:**
   ```bash
   make test          # All tests against Firestore emulator
   make lint          # ruff + mypy
   ```

2. **Smoke test succeeds locally:**
   ```bash
   make build
   make up
   make seed          # Load strategy + sample stocks
   make smoke         # Health check + quick analysis
   ```

3. **All secrets configured in `.env`:**
   - `GCP_PROJECT_ID` — your production Firestore project
   - `TELEGRAM_BOT_TOKEN` — from @BotFather
   - `TELEGRAM_ALLOWED_CHAT_IDS` — your chat ID
   - `AI_API_KEY` — Anthropic or Bedrock credentials
   - `FIRESTORE_EMULATOR_HOST` — empty in production (real Firestore)

4. **Git is clean:**
   ```bash
   git status         # No uncommitted changes
   ```

---

## Deployment steps

### 1. Build the Docker image

```bash
docker build -t gcr.io/$PROJECT_ID/wolfiero-api:latest ./backend
```

### 2. Push to Google Container Registry

```bash
docker push gcr.io/$PROJECT_ID/wolfiero-api:latest
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy wolfiero-api \
  --image gcr.io/$PROJECT_ID/wolfiero-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 3600 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,TELEGRAM_BOT_TOKEN=$TOKEN,TELEGRAM_ALLOWED_CHAT_IDS=$CHAT_ID,AI_API_KEY=$API_KEY"
```

**Environment variables:**
- `GCP_PROJECT_ID`: Your Firestore project ID
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `TELEGRAM_ALLOWED_CHAT_IDS`: Your chat ID (comma-separated for multiple)
- `AI_API_KEY`: Anthropic API key (if using Claude)
- `LOG_LEVEL`: INFO (production) or DEBUG (troubleshooting)
- `FIRESTORE_EMULATOR_HOST`: Leave unset (uses real Firestore)

### 4. Verify deployment

```bash
# Get service URL
gcloud run services describe wolfiero-api --platform managed --region us-central1

# Test health endpoint
curl https://<service-url>/health
```

---

## Post-deployment monitoring

### Cloud Logging

View real-time logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wolfiero-api" \
  --limit 50 \
  --format json
```

Or in the Cloud Console:
- Go to Cloud Run → wolfiero-api → Logs
- Filter by severity (Errors first)
- Check timestamps for scan execution

### Scan execution

Once deployed, trigger a scan via API:

```bash
curl -X POST https://<service-url>/api/scanner/run \
  -H "Content-Type: application/json" \
  -d '{"trade_date": "2026-09-12"}'
```

Response: `{"status": "accepted", "run_id": "uuid", "trade_date": "2026-09-12"}`

Get results:
```bash
curl https://<service-url>/api/scanner/runs/<run_id>
curl https://<service-url>/api/scanner/candidates?date_param=2026-09-12
```

---

## Troubleshooting

### "Firestore permission denied" error

- Verify service account has `roles/datastore.user` on the project
- Check `GCP_PROJECT_ID` environment variable is set correctly
- Ensure Firestore database is created in the project (not missing)

### "Telegram message failed to send"

- Verify `TELEGRAM_BOT_TOKEN` is valid (test with `curl` to Telegram API)
- Verify `TELEGRAM_ALLOWED_CHAT_IDS` is your chat ID (get via @userinfobot)
- Check Cloud Logging for exact Telegram API error response

### "No bars found for symbol"

- Run `make seed` locally to verify sample data loads
- Check Firestore console: `stocks` collection should have NVDA, AAPL, TSLA, QQQ, SPY
- If missing, re-run seed or manually load via API

### "Timeout on large scan"

- Cloud Run default timeout is 15 min; we set 3600 (1 hour) in deploy command
- If scan takes >1 hour, increase `--timeout` in deploy command
- Monitor CPU + memory usage in Cloud Run metrics

---

## Rollback

To revert to a previous revision:

```bash
# List recent revisions
gcloud run revisions list --service wolfiero-api --platform managed --region us-central1

# Route 100% traffic to an old revision
gcloud run services update-traffic wolfiero-api --to-revisions OLD_REVISION_ID=100 --platform managed --region us-central1
```

---

## Local development (still uses docker-compose)

```bash
make build              # Build containers
make up                 # Start Firestore emulator + API
make seed               # Load initial data
make test-unit          # Fast unit tests (no Docker)
make test-integ         # Integration tests with emulator
make down               # Stop containers
```

Docker Compose still uses Firestore emulator for local dev. Production Cloud Run uses real Firestore.

---

## Cost tracking

**Firestore free tier:**
- 50K reads/day
- 20K writes/day
- 1GB storage

**This workload (typical):**
- 1 scan run: ~10 reads (universe check), ~100 writes (candidates)
- 1-2 scans/day = ~200 reads, ~200 writes
- Well under free tier limit

**Costs if exceeded:**
- Reads: $0.06 per 100K
- Writes: $0.18 per 100K
- Deletes: $0.02 per 100K
- Storage: $0.18 per GB/month

Monitor in Cloud Console → Firestore → Usage section.

---

## Production guidelines

1. **Never deploy with `FIRESTORE_EMULATOR_HOST` set** — it will use the local emulator, not real Firestore
2. **Always run full test suite before deploying** — `make test` against emulator
3. **Verify Telegram credentials work** — send a test message before deploying
4. **Monitor first scan** — watch Cloud Logging for errors
5. **Keep `.env` secure** — never commit it; use Secret Manager for production values

---

## Scheduled scans (future)

When ready to schedule scans automatically (e.g., 5:30 AM daily):

1. Create Cloud Scheduler job:
   ```bash
   gcloud scheduler jobs create http premarket-scan \
     --schedule "30 5 * * *" \
     --http-method POST \
     --uri https://<service-url>/api/scanner/run \
     --oidc-service-account-email <service-account-email> \
     --oidc-token-audience https://<service-url>
   ```

2. Test: `gcloud scheduler jobs run premarket-scan`

3. Monitor: Check Cloud Logging for execution

**Note:** In-process APScheduler will NOT work on Cloud Run (scale-to-zero incompatible). Use Cloud Scheduler + HTTP requests instead.
