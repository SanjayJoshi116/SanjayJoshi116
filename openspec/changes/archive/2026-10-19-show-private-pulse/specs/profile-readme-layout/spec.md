## MODIFIED Requirements

### Requirement: Accurate All projects counts
The All projects summary SHALL show the number of private projects and public repositories listed inside it, and the numbers MUST equal the entries actually listed, counting each member of a public group as one repository.

#### Scenario: Count matches list
- **WHEN** a visitor expands All projects
- **THEN** the number of private entries and the number of public repositories linked in the table (group members included) equal the counts shown in the summary line

#### Scenario: Forks and profile repo not counted
- **WHEN** the owner has forked public repositories and the profile repository
- **THEN** none of them are listed or counted

## ADDED Requirements

### Requirement: Pulse strip under the private cards
The Featured section SHALL show the pulse strip directly below the private cards row, at full width, without a link.

#### Scenario: Visitor skims Featured
- **WHEN** a visitor reaches the Featured section
- **THEN** they see the public cards, the private cards, then the pulse strip, in that order

### Requirement: Grouped repos shown as one row
Each public repo group SHALL appear as a single row in the All projects public table, after the individually listed repos. The row SHALL show the group title, its stack and its one-line description, and SHALL link every member repository. Initially the group "Early ML coursework" holds StartupSuccessPrediction, HousePricePrediction, CricketScore, CustomerSegmentation and MachineLearningPrograms.

#### Scenario: Initial group
- **WHEN** a visitor expands All projects
- **THEN** the public table has 4 rows (movie-app-v2, movie-dash-v2, tv-dash, Early ML coursework), and the last row links all 5 notebook repos

#### Scenario: Member still reachable
- **WHEN** a visitor clicks `CricketScore` in the Early ML coursework row
- **THEN** the CricketScore repository opens
