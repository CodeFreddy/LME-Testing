Feature: FX Conversion for Non-HKD Instruments
  SR-MR-012-A-1
  # paragraph_ids: MR-012-A-1
  FX Conversion for Non-HKD Instruments

  @positive @priority_high  # TC-SR-MR-012-A-1-positive-01
  Scenario: Convert Non-HKD Instrument Values to HKD Equivalent
    Given A portfolio containing non-HKD denominated instruments
    And Latest available FX rates are available at position snapshot capture time
    When The position snapshot is captured
    And The system converts contract values and market values to HKD equivalent using latest FX rates without haircut
    Then Contract values are correctly converted to HKD equivalent
    And Market values are correctly converted to HKD equivalent
    And No haircut is applied to the FX conversion

  @boundary @priority_high  # TC-SR-MR-012-A-1-boundary-01
  Scenario: FX Conversion at Dissemination Time Boundaries
    Given A non-HKD denominated instrument position
    And Position snapshot captured at dissemination time boundary (11:45 a.m., 5:00 p.m., or 9:00 p.m. HKT)
    When The system applies the latest available FX rate at the dissemination time
    And The system converts values to HKD equivalent
    Then The FX rate available at the specific dissemination time is correctly applied
    And Conversion is performed without haircut
    And HKD equivalent values are correctly calculated

  @data_validation @priority_high  # TC-SR-MR-012-A-1-data_validation-01
  Scenario: Validate Market Value Calculation Formula
    Given Position data with Position quantity and Instrument market price
    And Position quantity sign indicates long (positive) or short (negative) position
    When The system calculates Market value using the formula: Market value = Position quantity x Instrument market price
    And The system applies the sign determined by position quantity
    Then Market value equals Position quantity multiplied by Instrument market price
    And Negative quantity results in negative market value (short position)
    And Positive quantity results in positive market value (long position)
