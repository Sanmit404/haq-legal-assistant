# Architecture

```text
Streamlit UI
  ├─ Case workspace and session state
  ├─ Consent, masking, rate limit, and output review
  ├─ ModelClient interface
  │    ├─ Gemini REST adapter
  │    └─ OpenAI-compatible HTTPS adapter
  ├─ Domain models and provenance validation
  ├─ Curated route/source registry
  └─ Document layer
       ├─ PDF/text/image extraction
       ├─ DOCX/PDF/text/ICS export
       └─ encrypted portable backups
```

## Reliability boundaries

The model proposes structured output. Pydantic validates the response before it can be applied. Evidence claims receive `Source-supported` status only when the cited quote exists verbatim in an evidence item with a matching ID. Unknown source IDs and model-generated external URLs are removed.

The app never silently sends, files, notarises, signs, or marks a matter resolved. Users review document fields and confirm fulfilment. Urgent fraud and physical-danger signals interrupt ordinary case guidance with official emergency paths.

## Production work still required

This prototype intentionally avoids pretending to provide production guarantees. A real public release would need authenticated accounts, an audited encrypted database, per-user isolation tests, abuse controls, observability without case-content logging, legal and privacy review, a source-change process, professional escalation partnerships, recovery procedures, and external penetration testing.
