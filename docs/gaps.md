---
layout: page
title: GAPS
---

# GAPS

GAPS is the Governed Autonomy Process Specification profile. It describes how a governed process preserves accountability, authority, autonomy boundaries, evidence, escalation, approval, state, projection, verification, closure, and external control mappings when autonomous systems may participate.

GAPS is exploratory. It is not a replacement for established standards.

## Relationship to existing standards

Where existing standards already own a concept, GAPS should align with them rather than re-derive them:

- BPMN for structured process flow.
- CMMN for adaptive case-style work.
- DMN for decision and policy logic.
- OSCAL-style structures for control mappings, implementation status, and evidence.
- NIST AI RMF, ISO/IEC 42001, and the EU AI Act as governance and regulatory anchors where applicable.

The intended GAPS contribution is the Governed Autonomy profile layered over that substrate:

- autonomy tier
- authority plane
- gate type
- human accountability
- evidence contract
- escalation and approval separation
- canonical state and projection rule
- drift and freshness rule
- Governed Autonomy risk-pattern coverage
- external control mapping stubs

## Repository files

- [GAPS README](https://github.com/awjreynolds/governed-autonomy/blob/main/gaps/README.md)
- [Process schema](https://github.com/awjreynolds/governed-autonomy/blob/main/gaps/schema/ga-process.schema.json)
- [Implementation-map schema](https://github.com/awjreynolds/governed-autonomy/blob/main/gaps/schema/implementation.schema.json)
- [Reference examples](https://github.com/awjreynolds/governed-autonomy/tree/main/gaps/examples)
