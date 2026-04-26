Feature: Initial Margin HKv13 flat rate margin POC
  End-to-end POC for section 3.2.4.2 Flat Rate Margin.

  @IM-HK13-FLAT-RATE @poc @positive
  Scenario: HKv13 guide example produces flat rate margin of 15,180,000
    Given the HKv13 flat rate margin example portfolio is prepared
    When flat rate margin is calculated under section 3.2.4.2
    Then only dominant-side positions per sub-category are included
    And the flat rate margin equals 15,180,000 HKD

