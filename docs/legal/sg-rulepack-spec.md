# SG Rule Pack Spec (`sg_v1`)

## Format
JSON rule pack with:
- `rule_pack_id`, `version`, `jurisdiction`
- `citations` map
- ordered `nodes`

## Node Schema
- `id`: unique node identifier
- `phase`: subsistence | infringement | substantial_taking | exceptions
- `prompt`: user-facing legal question
- `required_facts`: fact keys used for confidence
- `required_nodes`: optional dependencies
- `eval`: deterministic expression
- `derive`: optional computed facts
- `legal_refs`: citation IDs

## Supported Eval Types
- `fact_bool`
- `fact_false`
- `all_true`
- `any_true`
- `score_gte`
- `all_nodes_true`

## Node Output
- `answer`: yes | no | unknown
- `confidence`: known evidence ratio
- `evidence_refs`: fact/node references
- `legal_refs`

## Risk Band
Derived using:
- subsistence gate
- similarity headline score
- infringement core nodes
- fair-use signal downgrade

Risk values: `low`, `medium`, `high`