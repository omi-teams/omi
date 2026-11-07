---
id: structure-example
summary: Example architecture map; copy to .omi/structure.md and adapt to enable `omi structure check` in the post-run hook
---
<!-- Rename to .omi/structure.md (id: structure) to turn the check on. One line per glob, first match wins. -->
<!-- - src/app/modules/*/domain/**           | domain      | entities, rules, ports        | imports: domain, shared -->
<!-- - src/app/modules/*/application/**      | application | use cases, module public API  | imports: application, domain, shared -->
<!-- - src/app/modules/*/adapters/inbound/** | adapter-in  | HTTP, CLI, UI entry points    | imports: application, domain, shared -->
<!-- - src/app/modules/*/adapters/outbound/**| adapter-out | DB, external clients, files   | imports: application, domain, shared -->
<!-- - src/app/platform/**                   | platform    | framework, config, wiring     | imports: domain, application, adapter-in, adapter-out, shared, platform -->
<!-- - src/app/shared/**                     | shared      | small kernel                  | imports: shared -->
<!-- - docs/**, README.md                    | docs        | documentation                 | imports: - -->
<!-- - tests/**                              | test        | mirrors the code tree         | imports: domain, application, adapter-in, adapter-out, platform, shared -->
<!-- - pyproject.toml, .omi/**, .github/**   | config      | tooling and CI config         | imports: - -->
