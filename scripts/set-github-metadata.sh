#!/usr/bin/env bash
set -euo pipefail
gh repo edit iamrichmack111/wize-wizard \
 --description "Strategy, planning, and execution workbench connecting structured reasoning, PERT estimates, tasks, communications, learning, evidence, and executable project plans." \
 --add-topic flask --add-topic python --add-topic strategy --add-topic strategic-planning \
 --add-topic project-management --add-topic decision-support --add-topic pert --add-topic risk-analysis \
 --add-topic task-management --add-topic learning-platform --add-topic docker --add-topic github-actions \
 --add-topic cicd --add-topic codeql --add-topic bandit --add-topic trivy --add-topic dependabot \
 --add-topic sqlite --add-topic d2 --add-topic richmackos
echo "✅ GitHub metadata updated"
