## ADDED Requirements

### Requirement: Collapsed system diagram
The Featured section SHALL include, after the private cards and after the pulse strip when it is present, a `<details>` element collapsed by default whose summary reads "How <project title> works". Expanded, it SHALL show the pipeline diagram at full width, with alt text that names the project and lists every stage title and detail in order.

#### Scenario: Default collapsed
- **WHEN** a visitor loads the profile
- **THEN** the "How SwingTrade AI works" summary is visible and the diagram is hidden until it is clicked

#### Scenario: Screen reader on the diagram
- **WHEN** a screen reader reaches the expanded diagram
- **THEN** it announces e.g. "SwingTrade AI daily flow: NSE data (752 stocks, daily), then Indicators (EMA, RSI, ATR, market regime), then 23 detectors (breakouts, pullbacks, reversals), then Scan + score (weighted score, veto layer), then Alerts (email, Telegram)"
