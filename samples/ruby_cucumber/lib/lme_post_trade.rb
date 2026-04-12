# frozen_string_literal: true

# LME Post-Trade Operations - Simulated API for testing
# This is a PROTOTYPE demonstrating the interface structure
# Replace with real API client implementation

module LME
  module PostTrade
    class << self
      # Contact Exchange regarding a rejected order
      # @param reason [String] rejection reason
      # @return [ContactResponse]
      def contact_exchange(reason:)
        # TODO: Replace with actual API call
        # response = RestClient.post("#{base_url}/post-trade/contact",
        #   { reason: reason, timestamp: Time.now.utc })

        # Prototype simulation
        ContactResponse.new(
          id: "CONTACT_#{Time.now.to_i}",
          status: 'RECORDED',
          reason: reason,
          recorded_at: Time.now.utc
        )
      end

      # Get contact record
      # @param reason [String]
      # @return [ContactResponse, nil]
      def get_contact(reason:)
        # TODO: Replace with actual lookup
        ContactResponse.new(
          id: "CONTACT_EXISTING",
          status: 'RECORDED',
          reason: reason,
          member_id: 'MEM_001'
        )
      end

      # Get compliance status for a trade
      # @param trade_id [String]
      # @return [String] COMPLIANT | NON_COMPLIANT
      def get_compliance_status(trade_id)
        # TODO: Replace with actual API call
        'COMPLIANT'
      end

      # Submit rules for adoption
      # @param rules [MatchingRules]
      # @return [AdoptionResult]
      def submit_adoption(rules)
        # TODO: Replace with actual API call
        AdoptionResult.new(
          id: "ADOPT_#{Time.now.to_i}",
          classification: 'Administrative_Procedures',
          adopted: true
        )
      end

      # Define matching rules
      # @param version [String]
      # @return [MatchingRules]
      def define_matching_rules(version: '1.0')
        # TODO: Replace with actual creation
        MatchingRules.new(
          id: "RULES_#{version}",
          version: version,
          type: 'matching_rules'
        )
      end

      # Initiate a matching action
      # @param action: [String]
      # @return [MatchingAction]
      def initiate_matching(action: 'trade_match')
        # TODO: Replace with actual API call
        MatchingAction.new(
          id: "MATCH_#{Time.now.to_i}",
          action: action,
          allowed: true,
          procedure_ref: 'matching_rules'
        )
      end

      # Create trade agreement
      # @return [TradeAgreement]
      def create_agreement
        # TODO: Replace with actual API call
        TradeAgreement.new(
          id: "AGREE_#{Time.now.to_i}",
          price_validation_required: true
        )
      end

      # Provide additional information for trade
      # @param trade_id [String]
      # @param details [Hash]
      def provide_info(trade_id, details)
        # TODO: Replace with actual API call
        InfoRequest.new(id: trade_id, details: details)
      end

      # Get info request for trade
      # @param trade_id [String]
      # @return [InfoRequest, nil]
      def get_info_request(trade_id)
        # TODO: Replace with actual lookup
        InfoRequest.new(id: trade_id, details: { 'action' => 'provide_info' })
      end

      # Release a position
      # @param trade_id [String]
      def release_position(trade_id)
        # TODO: Release held position
      end

      # Get administrative procedures
      # @return [Array<Procedure>]
      def get_administrative_procedures
        # TODO: Replace with actual API call
        [Procedure.new(name: 'matching_rules', active: true)]
      end

      # Check administrative procedure status
      # @param rules_id [String]
      # @return [ProcedureStatus]
      def check_administrative_procedures(rules_id)
        # TODO: Replace with actual API call
        ProcedureStatus.new(recognized: true, type: :matching_rules)
      end
    end

    # Value Objects

    class ContactResponse
      attr_reader :id, :status, :reason, :recorded_at, :member_id

      def initialize(id:, status:, reason:, recorded_at: nil, member_id: nil)
        @id = id
        @status = status
        @reason = reason
        @recorded_at = recorded_at
        @member_id = member_id
      end

      def recorded?
        @status == 'RECORDED'
      end
    end

    class AdoptionResult
      attr_reader :id, :classification, :adopted

      def initialize(id:, classification:, adopted:)
        @id = id
        @classification = classification
        @adopted = adopted
      end
    end

    class MatchingRules
      attr_reader :id, :version, :type

      def initialize(id:, version:, type:)
        @id = id
        @version = version
        @type = type
      end
    end

    class MatchingAction
      attr_reader :id, :action, :allowed, :procedure_ref

      def initialize(id:, action:, allowed:, procedure_ref: nil)
        @id = id
        @action = action
        @allowed = allowed
        @procedure_ref = procedure_ref
      end
    end

    class TradeAgreement
      attr_reader :id, :price_validation_required

      def initialize(id:, price_validation_required: true)
        @id = id
        @price_validation_required = price_validation_required
      end
    end

    class InfoRequest
      attr_reader :id, :details

      def initialize(id:, details:)
        @id = id
        @details = details
      end
    end

    class Procedure
      attr_reader :name, :active

      def initialize(name:, active:)
        @name = name
        @active = active
      end
    end

    class ProcedureStatus
      attr_reader :recognized, :type

      def initialize(recognized:, type:)
        @recognized = recognized
        @type = type
      end
    end
  end
end
