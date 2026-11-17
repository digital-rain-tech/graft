# Repository instructions

Read `CLAUDE.md` and `SAFETY.md` for architecture and confidentiality rules.

This source tree must remain safe for public release, even while the repository is private. Never commit customer or prospect names, identifying details, supplied files, real sample data, internal SQL/schema/business information, branding, internal notes, or generated copies. This includes filenames, tests, comments, documentation, commit messages, tags, and branch names.

Keep originals, investigation evidence, logs, staging files, and recovery copies outside repository directories in a private location. Use synthetic examples with generic identifiers or redistributable public vendor demonstrations. Partial masking or renaming does not establish that a customer document is safe.

Review actual staged contents, binaries, generated outputs, and Git metadata before publishing. A previous scrub and `.gitignore` do not protect against material reintroduced under another path. Do not add identifying incident details to public cleanup notes or regression tests.

The shared cross-repository policy is maintained privately under `augustinchan.dev/.claude/memory/xrepo-customer-confidentiality.md`.
