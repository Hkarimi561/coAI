# Approved documentation store

Every `*.md` file in this directory (recursively) is indexed into the vector database. It is the **first and highest-priority source** for the assistant.

- Add or edit files here, then press **Index changes** in *Admin → Documents* or run `docker compose exec backend python -m app.cli ingest`. Only new/changed files are re-indexed.
- `promoted/` is written by the application when an admin approves a document drafted from a solved conversation.
- `uploads/` receives files uploaded from the admin UI.
- Suggested structure for runbooks: `Symptoms`, `Root Cause`, `Resolution Steps`, `Verification`.

The documents in this folder are **samples** that demonstrate the format; replace them with your own procedures.
