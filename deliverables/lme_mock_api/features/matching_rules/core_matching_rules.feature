Feature: LME Matching Rules executable mock validation
  Scenarios derived from docs/materials/LME_Matching_Rules_Aug_2022.md.

  @MR-001 @positive
  Scenario: Capitalised terms use the LME Rulebook meaning
    Given a capitalised term is used without a local definition
    When the term is interpreted according to the LME Rulebook
    Then the terminology validation is accepted with LME Rulebook source

  @MR-003 @positive
  Scenario: Member contacts Exchange after price validation failure
    Given an order or trade fails the price validation check
    When the Member contacts the Exchange to explain the rationale as to the price
    Then the contact action is recorded as compliant

  @MR-003 @negative
  Scenario: Missing Exchange contact rationale is rejected
    Given an order or trade fails the price validation check
    When the Member does not contact the Exchange to explain the rationale
    Then the contact obligation is rejected for missing rationale

  @MR-004 @positive
  Scenario: Extension request is made at least 15 minutes before deadline
    Given a post-trade request has a relevant deadline
    When the request is submitted 16 minutes before the relevant deadline
    Then the request is accepted as timely

  @MR-004 @negative
  Scenario: Extension request is rejected when late
    Given a post-trade request has a relevant deadline
    When the request is submitted 14 minutes before the relevant deadline
    Then the request is rejected as a late submission

  @MR-007 @positive
  Scenario: Asian hours Client Contract submitted by 08:30
    Given an Asian business hours Client Contract is prepared
    When the trade is submitted to the Matching System
    Then the trade submission is accepted

  @MR-007 @negative
  Scenario: Asian hours Client Contract submitted after 08:30 is rejected
    Given an Asian business hours Client Contract is submitted after 08:30 London time
    When the trade is submitted to the Matching System
    Then the trade submission is rejected for missing the Asian-hours deadline

  @MR-046 @positive
  Scenario: UNA Give-Up process generates clearer half
    Given a Give-Up Executor trade half is entered within 10 minutes
    When the Give-Up trade is submitted
    Then the Matching System generates a Give-Up Clearer half with U account

  @MR-064 @positive
  Scenario: OTC Bring-On with complete prior evidence is accepted
    Given an OTC Bring-On transaction has complete prior OTC evidence
    When the OTC Bring-On transaction is validated
    Then the OTC Bring-On transaction is accepted

  @MR-071 @negative
  Scenario: Auction bid with invalid Auction ID is rejected
    Given an auction bid has an invalid Auction ID
    When the auction bid is submitted
    Then the auction bid is rejected for invalid or expired Auction ID

  @MR-075 @negative
  Scenario: OTC Bring-On cannot be used to avoid PTT
    Given an Inter-Office order uses OTC Bring-On to avoid PTT
    When the PTT applicability is validated
    Then the order is rejected for misuse of OTC Bring-On

