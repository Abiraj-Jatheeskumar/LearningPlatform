# Azure OpenAI Setup for Question Generation

## Current Issue
The AI question generator is failing because Azure OpenAI credentials are not configured on Heroku.

## Required Environment Variables

You need to set these on Heroku:

```bash
heroku config:set AZURE_OPENAI_KEY="your-api-key-here" --app learning-platform-backend-2026
heroku config:set AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com" --app learning-platform-backend-2026
heroku config:set AZURE_OPENAI_DEPLOYMENT="your-deployment-name" --app learning-platform-backend-2026
heroku config:set AZURE_OPENAI_API_VERSION="2025-01-01-preview" --app learning-platform-backend-2026
```

## How to Get Azure OpenAI Credentials

### Option 1: Use Existing Azure OpenAI
1. Go to Azure Portal: https://portal.azure.com
2. Navigate to your Azure OpenAI resource
3. Copy:
   - **Endpoint**: From "Keys and Endpoint" section
   - **API Key**: From "Keys and Endpoint" section
   - **Deployment Name**: From "Model deployments" section (e.g., "gpt-4", "gpt-35-turbo")

### Option 2: Create New Azure OpenAI Resource
1. Go to Azure Portal
2. Create new "Azure OpenAI" resource
3. Wait for approval (may take a few days)
4. Deploy a model (gpt-4 or gpt-35-turbo recommended)
5. Get credentials from "Keys and Endpoint"

### Option 3: Use Alternative Free AI (Temporary Workaround)

If you don't have Azure OpenAI access, you can temporarily use a free alternative:

**Groq (Free API)**:
```bash
# Sign up at https://console.groq.com
# Get free API key
heroku config:set GROQ_API_KEY="your-groq-key-here" --app learning-platform-backend-2026
```

Then modify `backend/src/services/ai_question_generator.py` to use Groq instead of Azure.

## Verify Configuration

After setting the variables, check they're set:
```bash
heroku config --app learning-platform-backend-2026 | Select-String -Pattern "AZURE"
```

## Test Question Generation

1. Upload a PDF/PPTX in the instructor dashboard
2. Click "Generate Questions"
3. Check Heroku logs if it fails:
   ```bash
   heroku logs --tail --app learning-platform-backend-2026
   ```

## Alternative: Manual Question Creation

Until AI is configured, you can:
1. Use the "Create Question" form in instructor dashboard
2. Manually enter questions one by one
3. Questions will work fine for triggering to students
