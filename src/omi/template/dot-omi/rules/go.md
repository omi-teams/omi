---
id: go
summary: Go code: errors, formatting, tests, concurrency
applies: **/*.go, go.mod
---
# go

- Run `gofmt` and `go vet`; fix what they report.
- Return errors, never panic outside `main`; wrap with `fmt.Errorf("doing x: %w", err)`.
- Pass `context.Context` first; do not store it in structs.
- Table-driven tests, `t.Helper()` in helpers, no sleeps; run `go test ./...`.
- Every goroutine has an owner and a way to stop; close channels only from the sender.
- Standard library first; no new module without a reason in the task.
