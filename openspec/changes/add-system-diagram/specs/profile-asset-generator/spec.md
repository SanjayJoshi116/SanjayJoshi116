## ADDED Requirements

### Requirement: Diagram defined in the data file
A private project in `data/profile.yml` MAY carry a `diagram` with 3 to 6 `stages`, each with a `title` and a `detail`. At most one project SHALL carry a diagram. The generator SHALL fail and write nothing when a diagram has fewer than 3 or more than 6 stages, when a second project carries one, or when a title or detail does not fit its box on the allowed number of lines.

#### Scenario: Stage edit
- **WHEN** the owner changes a stage's detail in `data/profile.yml` and the generator runs
- **THEN** `pipeline.svg` and the diagram alt text show the new detail, with no manual edit

#### Scenario: Too many stages
- **WHEN** a diagram lists 7 stages
- **THEN** the run fails naming the limit and writes nothing

#### Scenario: Text too long
- **WHEN** a stage title does not fit on one line of its box
- **THEN** the run fails naming the stage and writes nothing

### Requirement: Generated diagram region
The generator SHALL regenerate `pipeline.svg` and the README's `diagram` region from the diagram in `data/profile.yml`, with or without a token. The region SHALL be empty when no project carries a diagram, and `pipeline.svg` SHALL then not be written. The same marker and failure rules as the other generated regions SHALL apply.

#### Scenario: Missing diagram marker
- **WHEN** the `diagram` end marker is missing from the README
- **THEN** the run fails naming the marker and writes nothing

#### Scenario: No token
- **WHEN** the generator runs without `PROFILE_TOKEN`
- **THEN** `pipeline.svg` and the `diagram` region are rendered exactly as they would be with a token

### Requirement: Diagram leak check
The generator SHALL check the rendered `pipeline.svg` and the rendered `diagram` region for every private repository `owner/name` value and bare name from `data/profile.yml`, with the same matching rules as the README check, and fail before writing if any is found. The error MUST NOT print the value.

#### Scenario: Bare repo name in a stage
- **WHEN** a stage detail contains a private repository's bare name as a whole word
- **THEN** the run fails before writing, naming `assets/pipeline.svg`, and the error does not print the name
