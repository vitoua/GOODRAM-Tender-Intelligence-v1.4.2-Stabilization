# GOODRAM Tender Intelligence v1.4.2 Stabilization

## Locked working connectors
TED, Prozorro, Latvia IUB and EKAP Turkey. Their versions are recorded in `CONNECTOR_LOCKS.json`; SHA-256 hashes are generated in `CONNECTOR_HASHES.json`.

## Beta connectors
BZP Poland, Germany OCDS diagnostics, Czech NEN optimized mode, Slovakia UVO/EVO diagnostics, Lithuania CVP IS diagnostics, Hungary EKR diagnostics and Estonia RHR discovery.

## Translator V2: how to enable
The existing LibreTranslate mechanism remains available as V1. A new independent V2 uses Azure AI Translator and a JSON cache.

In Render, add:

- `AZURE_TRANSLATOR_KEY`
- `AZURE_TRANSLATOR_REGION`

Then redeploy. In **System status**, V2 should show `v2_enabled: true`. Use **Test translator**, **Translate**, or **Translate visible**. If V2 is not configured, the UI shows the exact missing-variable error. The cache is stored in `data/translations_v2.json`; on Render Free it is temporary and may be reset after a redeploy/restart.

## Other Render variable
`APIFY_API_TOKEN` is required for EKAP Turkey.

## UI
Select all / clear selection controls are restored for both countries and connectors.
