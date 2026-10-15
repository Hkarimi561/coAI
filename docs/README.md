# Approved documentation store

Every `*.md` file in this directory (recursively) is indexed into the vector database. It is the **first and highest-priority source** for the assistant.

- Add or edit files here, then press **Index changes** in *Admin → Documents* or run `docker compose exec backend python -m app.cli ingest`. Only new/changed files are re-indexed.
- `promoted/` is written by the application when an admin approves a document drafted from a solved conversation.
- `uploads/` receives files uploaded from the admin UI.
- Suggested structure for runbooks: `Symptoms`, `Root Cause`, `Resolution Steps`, `Verification`.

The documents in this folder are **samples** that demonstrate the format; replace them with your own procedures.

## Third-party documentation sets (not stored in git)

Large public documentation sets can be placed next to the runbooks and are indexed the same way. They are **ignored by git** (see the root `.gitignore`) because they are about 50 MB, change often and belong to other projects. Keep your own runbooks tracked; put the sets below back into `docs/` on any new machine and press **Index changes** (or run the `ingest` command above).

| Folder | Content | Format |
|---|---|---|
| `kubernetes/` | Kubernetes documentation (concepts, tasks, tutorials, reference) | `.md` |
| `react-docs/` | React documentation | `.md` |
| `angular-docs/` | Angular documentation | `.md` |
| `nginx-docs/` | Nginx documentation | `.md` |
| `nextjs-docs/` | Next.js documentation | `.mdx` |
| `shadcn-docs/` | shadcn/ui documentation | `.mdx` |
| `tailwind-docs/` | Tailwind CSS documentation | `.mdx` |

- Both **`.md` and `.mdx`** files are indexed. MDX pages are converted to plain Markdown first: `import`/`export` lines, JSX comments and component tags are removed (their text stays), and the page title comes from the front matter or `export const title`. Code blocks and inline code such as `` `<Image>` `` are kept as written.
- Respect each project's licence when you copy documentation into your deployment.
- To start without them, simply leave the folders out; the assistant then relies on your runbooks, confirmed solutions, the web and MCP tools.
