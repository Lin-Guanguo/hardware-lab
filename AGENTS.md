# Agent Instructions

## Scope and context

- This is one repository containing independent projects under `projects/`.
- Read the root README and the target project's README before making changes.
  Follow any more specific `AGENTS.md` inside that project.
- Work within the requested project. Change shared files only when the task
  requires it, and preserve unrelated work.
- Root documentation is navigation and common guidance. Keep implementation
  details, working commands, and next steps with the project that owns them.

## Development

- Prefer a simple, working implementation and shell-driven workflows on macOS.
- Reuse the project's examples and board support code before inventing drivers
  or introducing another framework.
- Keep each firmware project independently buildable. Pin the toolchain and
  dependencies needed to reproduce it; do not force unrelated projects to
  share versions.
- Do not extract shared components or scripts until multiple projects need
  them. Create directories when there is content to put in them.
- Preserve upstream licenses. Document imported source URLs and revisions;
  never copy a nested `.git` directory into this repository.
- Prefer English for code, comments, commit messages, and repository guidance.
  Use Chinese for user-facing discussion or experiment notes when appropriate.
- Use `lgg/` for working branch names. Do not push or publish unless requested.

## Hardware facts and verification

- Distinguish advertised specifications, user-reported purchases, received
  components, and measured behavior. Do not turn assumptions into pinouts or
  claim that an untested device feature works.
- Check the exact board revision, voltage requirements, and pin ownership
  before proposing wiring or changing hardware configuration.
- Keep firmware builds separate from flashing. Only flash when the current
  task authorizes device programming, after identifying the target device
  and the applicable recovery path.
- Stay within low-voltage electronics. The lava lamp keeps its original mains
  supply and is physically separate from the experimental electronics.
- Run checks relevant to the change. Report commands and results, and state
  explicitly when validation was build-only or hardware was unavailable.
- After substantive work, update the project README's current state and next
  step. Store wiring, measurements, and detailed findings in project docs.

## Files and credentials

- Track sources and reproducible configuration, not generated build trees,
  caches, temporary firmware, or serial logs.
- Keep credentials and local connection settings out of Git; provide examples
  with placeholders when configuration is required.
- Remove `.gitkeep` when a directory gains real tracked content.
- Keep long discussion archives in CyberMnema and link to the relevant note.
  Do not copy shopping screenshots into this repository.
