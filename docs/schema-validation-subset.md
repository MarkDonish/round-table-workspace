# Schema Validation Subset

Round Table Workspace schemas declare Draft 2020-12. At runtime, validation uses
`jsonschema.Draft202012Validator` when the optional `jsonschema` package is
installed. Fresh clone and release checks must also work without third-party
dependencies, so the repo keeps a no-dependency fallback validator.

The fallback validator currently supports the schema keywords used by checked-in
RTW schemas:

- `$ref` for local `#/...` references
- `type`, including union type arrays
- `required`, `properties`, `additionalProperties`
- `const`, `enum`
- `items`, `minItems`, `maxItems`, `uniqueItems`
- `minLength`, `pattern`, `format: date-time`
- `minimum`, `maximum`
- `allOf`, `anyOf`, `oneOf`, `not`
- `if`, `then`, `else`
- `dependentRequired`
- `minProperties`, `maxProperties`

Release checks include negative fixtures through `scripts/run_negative_fixtures.py`.
Those fixtures must fail. If a new schema needs Draft 2020-12 behavior outside
this list, either install and require `jsonschema` for that path or extend the
fallback before claiming the constraint is enforced.
