# Governed SDLC validation

This fixture is a dogfood package for Governed Autonomy runtime enforcement.

It proves:

- the SDLC sidecar is mechanically valid through `ga-lint`;
- every step has matching governed skill frontmatter;
- PreToolUse blocks prohibited mapped actions while a step is active;
- PreToolUse allows unmapped actions when no governed rule applies;
- investigation steps are read-only;
- PostToolUse keeps a step active when declared repo evidence is missing;
- declared evidence clears the active step when present;
- more than one evidence-producing step is simulated.

It does not prove the process is well-governed in production. It is a repeatable fixture for validating the Governed Autonomy tooling loop.
