# GitHub Pages Setup Guide

If you're encountering "Getting signed artifact URL failed" or "Cannot find any run" errors when deploying documentation, follow these steps to ensure GitHub Pages is properly configured.

## Required GitHub Pages Configuration

### 1. Enable GitHub Pages

1. Go to your repository: `https://github.com/mmornati/hass-mcp`
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select **GitHub Actions** (NOT "Deploy from a branch")
4. Save the changes

### 2. Create GitHub Pages Environment

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name it: `github-pages`
4. Click **Configure environment**
5. No additional configuration is needed - the default settings are fine
6. Click **Save protection rules** (even if there are no rules)

### 3. Verify Workflow Permissions

Ensure your workflow has the correct permissions:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### 4. Check Repository Settings

1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, ensure:
   - **Read and write permissions** is selected, OR
   - **Read repository contents and packages permissions** is selected
   - Ensure **Allow GitHub Actions to create and approve pull requests** is enabled (if applicable)

### 5. Verify Branch Protection (if enabled)

If you have branch protection enabled on `master`:
1. Go to **Settings** → **Branches**
2. Ensure **Allow GitHub Actions to create and approve pull requests** is enabled
3. Ensure the workflow has permission to push to protected branches

## Common Issues and Solutions

### Issue: "Cannot find any run with github.run_id"

**Solution**: This usually means:
- GitHub Pages environment doesn't exist (create it in Settings → Environments)
- Pages source is not set to "GitHub Actions" (change in Settings → Pages)
- Workflow permissions are insufficient

### Issue: "Getting signed artifact URL failed"

**Solution**: This can be caused by:
- GitHub Pages not enabled or misconfigured
- Environment permissions issue
- Artifact upload timing issue (should be resolved by our workflow structure)

### Issue: Workflow doesn't run

**Solution**: Check:
- Workflow file is in `.github/workflows/` directory
- Workflow file has correct YAML syntax
- Path filters are correct if you're using them
- Branch names match your default branch (master/main)

## Verification Steps

After configuring GitHub Pages:

1. **Check Pages is enabled**: Go to Settings → Pages, verify source is "GitHub Actions"
2. **Check environment exists**: Go to Settings → Environments, verify `github-pages` exists
3. **Run workflow manually**: Go to Actions tab, select "Deploy Documentation", click "Run workflow"
4. **Check workflow logs**: Review the build and deploy job logs for any errors
5. **Verify deployment**: Once successful, your docs should be available at:
   - `https://mmornati.github.io/hass-mcp/`

## Troubleshooting

If issues persist after configuration:

1. **Check GitHub Status**: Visit https://www.githubstatus.com/ to ensure GitHub Actions is operational
2. **Review workflow logs**: Check the Actions tab for detailed error messages
3. **Verify repository settings**: Ensure Pages source is set to "GitHub Actions"
4. **Try manual deployment**: Use "workflow_dispatch" to manually trigger and debug

## Reference

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Deploying to GitHub Pages with Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow)
