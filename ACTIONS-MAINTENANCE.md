# Actions maintenance — 2026-10-15

The existing five workflow entry points remain. Workflow paths, admission job names, approval records and write permissions are unchanged, so historical evidence continues to use the original proof checks.

`plugin-publish.yml` now runs `publication_gate.py` in a read-only job before setting up .NET. It reuses the actual source-update or label-admission upstream identity/maintainer checks. A source scan whose `propose` job was skipped returns `needed=false`; verification, publication and notification jobs then skip. A label approval requires the actual successful `admit` job. Invalid provenance fails rather than being silently treated as no updates. Manual publication/check-only still reaches the original publisher authorization checks.

All workflows use the local `prepare-validator` composite action. Every executable validator is still built from the explicitly checked-out trusted commit; candidate assemblies remain byte inputs. The write job deliberately retains its own build and full publication proof checks. This refactor does not reuse executable artifacts across approval boundaries or combine reader/writer permissions.

Validation: 127 Python tests (one existing skip); actionlint 1.7.12 reports only its lack of support for the existing `concurrency.queue` key. Keeping that established queue setting, the remaining lint checks pass. Actual Actions execution of the new checkout remains pending until this change is pushed. No candidate approvals, releases or source-update policies were changed during local checks.
