# Integration test setup

These steps describe a reference setup for running the SharePoint
integration suite. The names below (`rg-firefly-test`, `kv-firefly-test`,
etc.) are conventions, not hard requirements — every contributor can
provision an equivalent environment under their own Azure subscription
and Microsoft 365 tenant.

## Prerequisites

* Azure subscription with permission to create resource groups and a Key
  Vault.
* Azure AD tenant administrator (to register an application with
  `Sites.Selected`).
* Microsoft 365 tenant with permission to create a SharePoint site.
* `az` CLI 2.60+ logged into the target tenant.

## Step 1 — Create the resource group and Key Vault

```bash
az group create --name rg-firefly-test --location spaincentral
az keyvault create --name kv-firefly-test \
    --resource-group rg-firefly-test \
    --location spaincentral \
    --enable-rbac-authorization true
```

Grant your account permission to read/write secrets:

```bash
USER_ID=$(az ad signed-in-user show --query id -o tsv)
az role assignment create \
    --role "Key Vault Secrets Officer" \
    --assignee $USER_ID \
    --scope $(az keyvault show -n kv-firefly-test --query id -o tsv)
```

## Step 2 — Register the test app

```bash
az ad app create --display-name firefly-test
APP_ID=$(az ad app list --display-name firefly-test --query "[0].appId" -o tsv)
az ad sp create --id $APP_ID
az ad app credential reset --id $APP_ID --display-name client-secret \
    --query "password" -o tsv > /tmp/client-secret
```

Add the secret to the Key Vault:

```bash
az keyvault secret set --vault-name kv-firefly-test \
    --name firefly-test-client-secret \
    --file /tmp/client-secret
```

## Step 3 — Grant `Sites.Selected` permission on the test site

In the Azure portal, open **App registrations → firefly-test → API
permissions** and add **Microsoft Graph → Application → Sites.Selected**.
Click **Grant admin consent**.

Then grant the app access to a single test site (replace placeholders):

```bash
SITE_ID="<your-test-site-id>"
az rest --method post \
    --url "https://graph.microsoft.com/v1.0/sites/$SITE_ID/permissions" \
    --body '{
      "roles": ["read", "write"],
      "grantedToIdentities": [{
        "application": {"id": "'$APP_ID'", "displayName": "firefly-test"}
      }]
    }'
```

## Step 4 — (Optional) Federated credential for CI

For GitHub Actions:

```bash
az ad app federated-credential create --id $APP_ID --parameters '{
  "name": "github-firefly-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:fireflyframework/fireflyframework-agentic:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

CI then uses the OIDC tokens to acquire a Graph token without static
secrets in the repository.

## Step 5 — Set environment variables for the test runner

```bash
export FIREFLY_TEST_TENANT_ID="<your-tenant-id>"
export FIREFLY_TEST_CLIENT_ID="$APP_ID"
export FIREFLY_TEST_CLIENT_SECRET="$(cat /tmp/client-secret)"
export FIREFLY_TEST_DRIVE_ID="<your-test-drive-id>"
```

Run the integration suite:

```bash
pytest tests/integration -v
```

Without these variables the suite skips automatically; only the unit
tests under `tests/test_ingestion/` run.
