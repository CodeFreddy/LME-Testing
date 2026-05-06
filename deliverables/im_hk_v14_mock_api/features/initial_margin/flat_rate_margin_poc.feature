Feature: Initial Margin HKv14 flat rate margin POC
  End-to-end POC for section 3.2.4.2 Flat Rate Margin.

  @IM-HK14-FLAT-RATE @poc @positive
  Scenario: HKv14 guide three-term example produces flat rate margin of 15,180,000
    Given the HKv14 flat rate margin example portfolio is prepared
    When flat rate margin is calculated under section 3.2.4.2
    Then only dominant-side positions per sub-category are included
    And the flat rate margin equals 15,180,000 HKD
