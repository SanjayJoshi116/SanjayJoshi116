## MODIFIED Requirements

### Requirement: Scheduled and push-triggered regeneration
A GitHub Actions workflow SHALL regenerate the assets daily and on any push that changes `data/profile.yml` or the asset templates. It SHALL also be manually runnable. In addition, it SHALL poll hourly between 06:17 and 23:17 IST and regenerate only when a repository's last push time has changed since the last successful render. The polled set SHALL be the owner's public repositories, except hidden ones and the profile repository itself, and the private repositories named in `projects.private[].card.repo`, and no other private repository. The first poll of each IST calendar day SHALL regenerate, so relative ages stay current. The daily, push and manual runs SHALL regenerate regardless of the poll result.

#### Scenario: Daily refresh
- **WHEN** the daily schedule fires
- **THEN** the workflow runs and refreshes stars, stats, and featured selection

#### Scenario: Push to a watched repo during the day
- **WHEN** a private card repository or a public repository is pushed at 14:05 IST
- **THEN** the 14:17 IST poll detects the change and regenerates the assets

#### Scenario: Nothing pushed since the last render
- **WHEN** an hourly poll fires and no polled repository has a newer push time than at the last successful render
- **THEN** the run ends without rendering or committing

#### Scenario: Asset commit does not re-trigger
- **WHEN** a render commits refreshed assets to the profile repository and nothing else is pushed
- **THEN** the next poll in the same IST day ends without rendering

#### Scenario: New day
- **WHEN** the first poll of an IST calendar day fires
- **THEN** it regenerates the assets even if no repository was pushed

#### Scenario: Night hours
- **WHEN** a watched repository is pushed at 23:40 IST
- **THEN** no poll runs before 06:17 IST, and the 06:17 IST poll regenerates the assets

#### Scenario: Failed render is retried
- **WHEN** a poll detects a change but the render fails
- **THEN** the next poll detects the same change and renders again

#### Scenario: Missing poll state
- **WHEN** no saved fingerprint from a previous render is available
- **THEN** the poll treats it as changed and regenerates the assets

## ADDED Requirements

### Requirement: Poll leaks nothing to logs
The poll SHALL NOT print repository names, push times, or the fingerprint value. Its log output SHALL be limited to whether a change was detected. If the poll cannot compute the fingerprint, it SHALL treat the result as changed without printing the error detail, so the render runs and reports any failure itself.

#### Scenario: Poll log content
- **WHEN** a poll run's logs are viewed on the public repository
- **THEN** they show only a changed/unchanged result and contain no repository name, push time, or fingerprint

#### Scenario: Poll API failure
- **WHEN** the API fails while the poll computes the fingerprint
- **THEN** the poll reports "changed" without error detail, and the render step runs under its existing failure rules
