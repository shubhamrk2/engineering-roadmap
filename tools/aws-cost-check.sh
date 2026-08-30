#!/usr/bin/env bash
#
# aws-cost-check.sh — find everything in your AWS account that bills money.
#
# Every API call in this script is FREE. Cost Explorer (the only paid API,
# at $0.01/request) is NOT used — run the console UI for cost figures instead.
#
# Usage:
#   ./aws-cost-check.sh                        # uses AWS_PROFILE or default
#   ./aws-cost-check.sh badgedesk-admin        # explicit profile
#
set -uo pipefail

PROFILE="${1:-${AWS_PROFILE:-default}}"
AWS="aws --profile $PROFILE"

BOLD="\033[1m"; DIM="\033[2m"; RED="\033[0;31m"; YELLOW="\033[0;33m"
GREEN="\033[0;32m"; CYAN="\033[0;36m"; RESET="\033[0m"

FINDINGS=0

hdr()  { echo -e "\n${BOLD}$1${RESET}"; }
hit()  { echo -e "  ${RED}[BILLING]${RESET} $1"; FINDINGS=$((FINDINGS+1)); }
warn() { echo -e "  ${YELLOW}[CHECK]  ${RESET} $1"; FINDINGS=$((FINDINGS+1)); }
ok()   { echo -e "  ${GREEN}[clean] ${RESET} $1"; }
note() { echo -e "  ${DIM}$1${RESET}"; }

echo -e "${BOLD}=========================================${RESET}"
echo -e "${BOLD}  AWS billable-resource sweep${RESET}"
echo -e "${BOLD}=========================================${RESET}"

# ── identity ──────────────────────────────────────────────────────────────────
IDENTITY=$($AWS sts get-caller-identity --output json 2>/dev/null) || {
    echo -e "${RED}Not authenticated.${RESET} Run:  aws sso login --profile $PROFILE"
    exit 1
}
ACCOUNT=$(echo "$IDENTITY" | jq -r .Account)
ARN=$(echo "$IDENTITY" | jq -r .Arn)
echo -e "\n  Account: ${CYAN}${ACCOUNT}${RESET}"
echo -e "  Identity: ${DIM}${ARN}${RESET}"

# ── global (region-independent) ───────────────────────────────────────────────
hdr "GLOBAL SERVICES"

BUCKETS=$($AWS s3api list-buckets --query 'Buckets[].Name' --output text 2>/dev/null)
if [ -n "$BUCKETS" ] && [ "$BUCKETS" != "None" ]; then
    for B in $BUCKETS; do hit "S3 bucket: $B"; done
    note "storage + requests bill; check size with: aws s3 ls s3://<bucket> --recursive --summarize"
else
    ok "no S3 buckets"
fi

ZONES=$($AWS route53 list-hosted-zones --query 'HostedZones[].Name' --output text 2>/dev/null)
if [ -n "$ZONES" ] && [ "$ZONES" != "None" ]; then
    for Z in $ZONES; do hit "Route 53 hosted zone: $Z  (~\$0.50/month)"; done
else
    ok "no Route 53 hosted zones"
fi

# ── regional sweep ────────────────────────────────────────────────────────────
REGIONS=$($AWS ec2 describe-regions --query 'Regions[].RegionName' --output text 2>/dev/null)
if [ -z "$REGIONS" ]; then
    echo -e "${RED}Could not list regions.${RESET}"
    exit 1
fi

hdr "REGIONAL SWEEP"
note "scanning $(echo "$REGIONS" | wc -w) regions — takes ~60 s"

for R in $REGIONS; do
    A="$AWS --region $R"
    REGION_HITS=""

    # running EC2 instances
    OUT=$($A ec2 describe-instances \
            --filters Name=instance-state-name,Values=running \
            --query 'Reservations[].Instances[].[InstanceId,InstanceType]' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    EC2 running:        $(echo "$OUT" | tr '\n' ' ')\n"

    # unattached EBS volumes
    OUT=$($A ec2 describe-volumes \
            --filters Name=status,Values=available \
            --query 'Volumes[].[VolumeId,Size,VolumeType]' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    EBS unattached:     $(echo "$OUT" | tr '\n' ' ')\n"

    # attached EBS volumes still bill
    OUT=$($A ec2 describe-volumes \
            --filters Name=status,Values=in-use \
            --query 'Volumes[].[VolumeId,Size]' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    EBS in-use:         $(echo "$OUT" | tr '\n' ' ')\n"

    # unassociated Elastic IPs
    OUT=$($A ec2 describe-addresses \
            --query 'Addresses[?AssociationId==null].PublicIp' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    Elastic IP idle:    $OUT  (~\$3.60/mo each)\n"

    # snapshots
    OUT=$($A ec2 describe-snapshots --owner-ids self \
            --query 'Snapshots[].[SnapshotId,VolumeSize]' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    Snapshots:          $(echo "$OUT" | tr '\n' ' ')\n"

    # NAT gateways — the expensive one
    OUT=$($A ec2 describe-nat-gateways \
            --filter Name=state,Values=available \
            --query 'NatGateways[].NatGatewayId' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    NAT GATEWAY:        $OUT  (~\$32/mo each)\n"

    # load balancers
    OUT=$($A elbv2 describe-load-balancers \
            --query 'LoadBalancers[].LoadBalancerName' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    Load balancer:      $OUT  (~\$16-25/mo each)\n"

    # RDS
    OUT=$($A rds describe-db-instances \
            --query 'DBInstances[].[DBInstanceIdentifier,DBInstanceClass]' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && REGION_HITS+="    RDS instance:       $(echo "$OUT" | tr '\n' ' ')\n"

    # EKS — very expensive
    OUT=$($A eks list-clusters --query 'clusters' --output text 2>/dev/null)
    [ -n "$OUT" ] && [ "$OUT" != "None" ] && REGION_HITS+="    EKS CLUSTER:        $OUT  (~\$73/mo each)\n"

    # Secrets Manager
    OUT=$($A secretsmanager list-secrets \
            --query 'SecretList[].Name' --output text 2>/dev/null)
    [ -n "$OUT" ] && [ "$OUT" != "None" ] && REGION_HITS+="    Secret:             $OUT  (\$0.40/mo each)\n"

    # customer-managed KMS keys
    OUT=$($A kms list-aliases \
            --query 'Aliases[?starts_with(AliasName, `alias/aws/`)==`false`].AliasName' \
            --output text 2>/dev/null)
    [ -n "$OUT" ] && [ "$OUT" != "None" ] && REGION_HITS+="    KMS key:            $OUT  (\$1/mo each)\n"

    # AWS Config recorder
    OUT=$($A configservice describe-configuration-recorders \
            --query 'ConfigurationRecorders[].name' --output text 2>/dev/null)
    [ -n "$OUT" ] && [ "$OUT" != "None" ] && REGION_HITS+="    AWS Config ON:      $OUT  (bills per config item)\n"

    # CloudTrail trails beyond the free one
    OUT=$($A cloudtrail describe-trails \
            --query 'trailList[].Name' --output text 2>/dev/null)
    [ -n "$OUT" ] && [ "$OUT" != "None" ] && REGION_HITS+="    CloudTrail:         $OUT  (S3 storage + PUTs)\n"

    if [ -n "$REGION_HITS" ]; then
        echo -e "\n  ${YELLOW}${R}${RESET}"
        echo -ne "$REGION_HITS"
        FINDINGS=$((FINDINGS+1))
    fi
done

# ── budgets ───────────────────────────────────────────────────────────────────
hdr "BUDGETS"
$AWS budgets describe-budgets --account-id "$ACCOUNT" \
    --query 'Budgets[].[BudgetName,BudgetLimit.Amount,CalculatedSpend.ActualSpend.Amount]' \
    --output table 2>/dev/null || note "no budgets readable"

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}=========================================${RESET}"
if [ "$FINDINGS" -eq 0 ]; then
    echo -e "${GREEN}  Account is clean — nothing billable found.${RESET}"
    echo -e "${DIM}  If you still see charges, they are likely${RESET}"
    echo -e "${DIM}  data transfer or already-deleted resources${RESET}"
    echo -e "${DIM}  billed in arrears. Check again tomorrow.${RESET}"
else
    echo -e "${YELLOW}  $FINDINGS area(s) with billable resources.${RESET}"
    echo -e "${DIM}  Review above, then delete what you do not need.${RESET}"
fi
echo -e "${BOLD}=========================================${RESET}"
echo ""
echo -e "  Exact costs (free, console only):"
echo -e "  ${CYAN}Billing → Cost Explorer → Group by: Service${RESET}"
echo ""
