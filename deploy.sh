#!/usr/bin/env bash
# Midnight Core — ECS deploy script
# Usage: source .env && ./deploy.sh
set -euo pipefail

REGION="us-east-1"
ACCOUNT="989615776408"
ECR_REPO="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/midnightcore"
CLUSTER="default"
SERVICE="midnightcore-78b3"
TASK_FAMILY="default-midnightcore-78b3"

DATE=$(date +%Y%m%d)
SHA=$(git rev-parse --short HEAD)
TAG="cc-deploy-${DATE}-${SHA}"

echo "==> Building ${TAG}"
docker build -t "midnightcore:${TAG}" .

echo "==> Pushing to ECR"
aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${ECR_REPO}"
docker tag "midnightcore:${TAG}" "${ECR_REPO}:${TAG}"
docker push "${ECR_REPO}:${TAG}"

echo "==> Registering new task definition"
python3 - <<PYEOF
import json, subprocess

result = subprocess.run(
    ["aws", "ecs", "describe-task-definition",
     "--task-definition", "${TASK_FAMILY}",
     "--region", "${REGION}"],
    capture_output=True, text=True, check=True,
)
task = json.loads(result.stdout)["taskDefinition"]

# Update image to new tag
task["containerDefinitions"][0]["image"] = "${ECR_REPO}:${TAG}"

env = task["containerDefinitions"][0].setdefault("environment", [])

# Update DEPLOY_NONCE
updated = False
for e in env:
    if e["name"] == "DEPLOY_NONCE":
        e["value"] = "${DATE}-${SHA}"
        updated = True
if not updated:
    env.append({"name": "DEPLOY_NONCE", "value": "${DATE}-${SHA}"})

# Inject PLATFORM_ADMIN_EMAILS from local env if set
admin_emails = "${PLATFORM_ADMIN_EMAILS:-}"
if admin_emails:
    found = any(e["name"] == "PLATFORM_ADMIN_EMAILS" for e in env)
    if found:
        for e in env:
            if e["name"] == "PLATFORM_ADMIN_EMAILS":
                e["value"] = admin_emails
    else:
        env.append({"name": "PLATFORM_ADMIN_EMAILS", "value": admin_emails})

# Strip read-only fields before registering
for key in ["taskDefinitionArn", "revision", "status", "requiresAttributes",
            "placementConstraints", "compatibilities", "registeredAt", "registeredBy"]:
    task.pop(key, None)

with open("/tmp/midnight_task_def.json", "w") as f:
    json.dump(task, f)
print("Task definition staged.")
PYEOF

NEW_ARN=$(aws ecs register-task-definition \
  --cli-input-json "file:///tmp/midnight_task_def.json" \
  --region "${REGION}" \
  --query "taskDefinition.taskDefinitionArn" \
  --output text)

echo "==> New task: ${NEW_ARN}"

echo "==> Updating service"
aws ecs update-service \
  --cluster "${CLUSTER}" \
  --service "${SERVICE}" \
  --task-definition "${NEW_ARN}" \
  --region "${REGION}" \
  --query "service.serviceArn" \
  --output text

echo ""
echo "==> Deployed ${TAG}"
echo "    ECS is pulling the new image — live in ~2 minutes."
