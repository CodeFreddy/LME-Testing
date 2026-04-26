Feature: Non-HKD Instrument FX Conversion
  SR-MR-012-C-1
  # paragraph_ids: MR-012-C-1
  Non-HKD Instrument FX Conversion

  @positive @priority_high  # TC-SR-MR-012-C-1-positive-01
  Scenario: Non-HKD instrument converted to HKD equivalent
    Given A position exists for a non-HKD denominated instrument
    And The latest available FX rate is accessible
    And The position snapshot is being captured
    When The system converts contract value and market value to HKD equivalent
    Then Contract value is converted using the latest FX rate without haircut
    And Market value is converted using the latest FX rate without haircut
    And HKD equivalent values are calculated and stored

  @boundary @priority_high  # TC-SR-MR-012-C-1-boundary-01
  Scenario: FX conversion at position snapshot capture time
    Given A non-HKD instrument position exists
    And Position snapshot capture time is around 11:45 a.m., 5:00 p.m., or 9:00 p.m. HKT
    When The position snapshot is captured at dissemination time
    Then The latest available FX rate at snapshot time is applied
    And Conversion is performed without haircut
    And HKD equivalent values reflect the FX rate at snapshot capture moment

  @data_validation @priority_high  # TC-SR-MR-012-C-1-data_validation-01
  Scenario: FX rate data validation for conversion
    Given A non-HKD instrument position exists
    And FX rate data is available in the system
    When The system validates FX rate data before conversion
    Then FX rate is a valid numeric value
    And FX rate is the latest available rate
    And No haircut is applied to the FX rate
    And Converted HKD equivalent values are valid numeric values
