# LLM Provider Switch (Claude ↔ Bedrock)

This document explains how to switch between Claude (Anthropic) and Bedrock (AWS) as your LLM provider.

## Current Setup

By default, the system uses **Claude** (Anthropic API). Both Claude and Bedrock implementations are ready to use.

## Switching to Bedrock

When your Claude credits run out (or whenever you want to switch), follow these steps:

### 1. Get AWS Credentials

1. Create an AWS account or log into an existing one
2. Go to **IAM** → **Users** → Create a new user for this purpose
3. Create an access key (save the `Access Key ID` and `Secret Access Key`)
4. Attach the **AmazonBedrockFullAccess** policy to the user
5. Or create a custom policy with permissions for the Bedrock API

### 2. Enable Bedrock Model Access

1. Go to **Bedrock** → **Model access** in the AWS Console
2. Click **Manage model access**
3. Enable access to **Claude 3 Opus** (or your preferred Claude model)
4. Accept the terms

### 3. Update .env

Edit `.env` and set:

```bash
# Switch to Bedrock
AI_PROVIDER=bedrock

# AWS credentials
AWS_REGION=us-east-1              # or your preferred region
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJa...

# Bedrock model ID (find in AWS Bedrock console)
BEDROCK_MODEL_ID=anthropic.claude-opus-5-20250514-v1:0

# Keep Claude settings but they won't be used
AI_API_KEY=sk-ant-...
AI_MODEL=claude-opus-5
```

### 4. Restart Services

```bash
make build      # Rebuild with boto3 dependency
make down       # Stop old services
make up         # Start with Bedrock
```

### 5. Verify

Check logs:

```bash
make logs
# Look for: "LLM provider initialized: bedrock"
```

Test health endpoint:

```bash
curl http://localhost:8001/health
# Should show: "provider": "bedrock"
```

## Switching Back to Claude

If you want to return to Claude:

```bash
# .env
AI_PROVIDER=claude
AI_API_KEY=sk-ant-...
```

Restart:

```bash
make down && make up
```

## Cost Comparison

- **Claude (Anthropic)**: Pay-as-you-go, $3-$15 per 1M tokens depending on model
- **Bedrock (AWS)**: Pay-as-you-go, ~$3-$15 per 1M tokens + AWS infrastructure costs

Both are roughly equivalent in cost. Bedrock may be preferable if you're already using AWS.

## Instrumentation & Monitoring

Both providers log their API calls with:
- `model_id` / `model`
- `max_tokens`
- `tool_count`
- Execution time

These logs are structured (JSON) and can be sent to CloudWatch, DataDog, etc.

### Adding Custom Metrics

To add usage tracking, update `llm_provider.py`:

```python
def create_message(...):
    logger.info(
        "llm_call",
        provider=self.provider_name,
        model=model,
        tokens_used=response.usage.output_tokens,
    )
```

Then wire these logs to your monitoring system.

## Known Differences

| Aspect | Claude | Bedrock |
|--------|--------|---------|
| Latency | ~2-5s | ~2-5s |
| Tool use format | Native Anthropic | Converse API |
| Pricing | Anthropic rates | AWS rates |
| Region | Global | AWS regions |
| Availability | Always available | Requires model access |

## Troubleshooting

### "UnknownModel" error

The model ID may have changed. Check AWS Bedrock console for the current ID format.

### "AccessDenied" error

- Verify IAM user has `bedrock:InvokeModel` permission
- Check model access is enabled in Bedrock console
- Verify AWS credentials are correct

### Slow responses

- Bedrock may be in a different region; try `us-east-1` or `us-west-2`
- Check CloudWatch logs in AWS Console for throttling

## Future: Permanent Switch

Once you're satisfied with Bedrock and the old Claude credits are gone:

1. Remove the `AI_PROVIDER=claude` branch logic
2. Delete Claude implementation from `llm_provider.py`
3. Simplify to Bedrock-only codebase

This will be a separate PR/commit when the time comes.
