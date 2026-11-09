---
id: structure-example
summary: Example architecture map covering the whole repo root; copy to .omi/structure.md and adapt (omi-idea proposes it after the stack)
---
<!-- Rename to .omi/structure.md (id: structure): write steps need it and the post-run hook checks it. One line per glob, first match wins. -->
<!-- Give every root entry a line: `omi structure check` reports root folders the map does not match. -->
<!-- `imports:` lists the other layers a layer may import; a layer may always import itself, so `imports: -` means nothing outside its own layer. -->
<!-- - src/app/modules/*/domain/**           | domain      | entities, rules, ports        | imports: shared -->
<!-- - src/app/modules/*/application/**      | application | use cases, module public API  | imports: domain, shared -->
<!-- - src/app/modules/*/adapters/inbound/** | adapter-in  | HTTP, CLI, UI entry points    | imports: application, domain, shared -->
<!-- - src/app/modules/*/adapters/outbound/**| adapter-out | DB, external clients, files   | imports: application, domain, shared -->
<!-- - src/app/platform/**                   | platform    | framework, config, wiring     | imports: domain, application, adapter-in, adapter-out, shared -->
<!-- - src/app/shared/**                     | shared      | small kernel                  | imports: - -->
<!-- - database/**                           | data        | migrations, seeds, schema     | imports: - -->
<!-- - tests/**                              | test        | mirrors the code tree         | imports: domain, application, adapter-in, adapter-out, platform, shared -->
<!-- - docs/**, README.md, LICENSE           | docs        | documentation                 | imports: - -->
<!-- - deploy/**                             | config      | deployment manifests          | imports: - -->
<!-- - scripts/**                            | platform    | developer and CI scripts      | imports: shared -->
<!-- - .github/**, .githooks/**, .omi/**     | config      | CI, git hooks, omi config     | imports: - -->
<!-- - pyproject.toml, .gitignore, .gitattributes | config | tooling config              | imports: - -->
