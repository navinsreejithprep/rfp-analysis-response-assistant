> **SYNTHETIC / DEMO DATA** for the fictitious company NorthPeak Digital Partners.

# AI & Data Capabilities

## Applied AI / GenAI
NorthPeak's AI & Data Engineering group designs retrieval-augmented generation (RAG) systems,
agentic workflows (including LangGraph-orchestrated multi-step pipelines), and structured
extraction pipelines using large language models (OpenAI and Anthropic model families). Standard
practice includes evaluation datasets, groundedness checks against source documents, and human
review gates for any output that informs a customer-facing decision.

## Machine Learning
NorthPeak builds classical ML pipelines (scikit-learn, XGBoost) for forecasting, churn modeling,
and anomaly detection, typically deployed via containerized inference services with monitoring
for data and prediction drift.

## MLOps
NorthPeak uses MLflow for experiment tracking and model registry, and deploys models via
Kubernetes-based inference services with blue/green rollout. NorthPeak has not implemented
on-device / edge inference deployments in past engagements.

## Data Governance
NorthPeak's data engineering practice includes data lineage tracking (via dbt docs / OpenLineage)
and role-based access control on warehouse layers. NorthPeak has supported clients in preparing
for GDPR data-subject-request workflows, but does not itself act as a data controller for client
data.

## Limitations
NorthPeak has not built production speech-to-text or computer-vision systems for regulated
medical-device use cases. Any RFP requirement in that specific area would require additional
evidence beyond what is captured here.
