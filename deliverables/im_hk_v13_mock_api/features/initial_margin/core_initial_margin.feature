Feature: Initial Margin HKv13 executable mock validation
  Scenarios derived from Initial Margin Calculation Guide HKv13.

  @IM-HK13-RPF @positive
  Scenario: Risk Parameter File contains required fields
    Given an Initial Margin Risk Parameter File contains required global fields and supported FieldType records
    When the risk parameter file is validated
    Then the risk parameter file validation is accepted

  @IM-HK13-RPF @negative
  Scenario: Risk Parameter File missing SVaR confidence level is rejected
    Given an Initial Margin Risk Parameter File is missing the SVaR confidence level
    When the risk parameter file is validated
    Then the risk parameter file validation is rejected for missing global fields

  @IM-HK13-POS @positive
  Scenario: Position market value is calculated from quantity and price
    Given a portfolio position has quantity and market price
    When the positions are normalized
    Then the market value equals quantity times market price

  @IM-HK13-MRC @positive
  Scenario: Portfolio margin and flat rate margin components are calculated
    Given a mixed Tier P and Tier N portfolio has risk parameters
    When market risk components are calculated
    Then portfolio margin and flat rate margin components are returned

  @IM-HK13-ROUND @positive
  Scenario: Aggregated market risk component is rounded up
    Given market risk total is below a rounding unit
    When the margin is aggregated
    Then the market risk is rounded up before offsets and add-ons

  @IM-HK13-MTM @positive
  Scenario: Favorable MTM is separated from MTM requirement
    Given MTM items net to a favorable MTM amount
    When MTM is calculated
    Then favorable MTM is separated from MTM requirement

  @IM-HK13-CA @positive
  Scenario: Corporate action creates adjusted and entitlement positions
    Given a stock split and cash dividend apply before the ex-date
    When corporate action adjustment is performed
    Then the adjusted position and benefit entitlement position are produced

  @IM-HK13-NET @positive
  Scenario: Cross-day netting groups positions by instrument
    Given positions exist across trade dates for the same instrument
    When cross-day netting is performed
    Then one netted position is returned for the instrument

  @IM-HK13-FX @positive
  Scenario: Cross-currency MTM netting applies directional haircuts
    Given MTM exists in multiple currencies with FX haircuts
    When cross-currency MTM netting is performed
    Then positive and favorable MTM use directional haircut conversion

  @IM-HK13-INTRADAY @positive
  Scenario: Intraday 11:00 run reduces due-today long positions
    Given due-today long positions and an offset ratio exist at 11:00
    When intraday MTM treatment is applied
    Then the due-today long position is reduced by the offset ratio

  @IM-HK13-INTRADAY @positive
  Scenario: Intraday 14:00 run excludes due-today positions
    Given due-today positions exist at 14:00
    When intraday MTM treatment is applied
    Then due-today positions are excluded

