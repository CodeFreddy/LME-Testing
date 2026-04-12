# frozen_string_literal: true

# LME API Client - Simulated API for testing
# This is a PROTOTYPE demonstrating the interface structure
# Replace with real API client implementation

module LME
  module API
    # API Client for LME trading operations
    class Client
      attr_reader :base_url, :token

      def initialize(base_url:, token: nil)
        @base_url = base_url
        @token = token || LME::Client.token
      end

      # Validate terminology against rulebook
      # @param document [Document]
      # @return [ValidationResult]
      def validate_terminology(document)
        # TODO: Replace with actual API call
        # response = post('/terminology/validate', document.to_h)

        # Prototype simulation
        ValidationResult.new(
          compliant: document.terms_defined != false,
          source: 'LME Rulebook',
          errors: document.terms_conflict ? ['TERM_DEVIATION'] : []
        )
      end

      # Validate price for a trade
      # @param params [Hash] order parameters
      # @return [ValidationResult]
      def check_price_validation(params)
        # TODO: Replace with actual API call
        # response = post('/orders/validate_price', params)

        # Prototype: reject obviously invalid prices
        price = params[:price].to_f
        if price > 99999 || price < 0
          ValidationResult.new(
            status: 'FAILED',
            errors: ['PRICE_VALIDATION_FAILED'],
            rejection_reason: "Invalid price: #{price}"
          )
        else
          ValidationResult.new(status: 'PASSED', errors: [])
        end
      end

      # Submit a trade for matching
      # @param params [Hash] trade parameters
      # @return [TradeSubmission]
      def submit_trade(params)
        # TODO: Replace with actual API call
        TradeSubmission.new(
          id: "TRADE_#{Time.now.to_i}",
          status: 'SUBMITTED',
          params: params
        )
      end

      # Re-submit trade in original form after correction
      # @param trade_id [String]
      # @param original_form [Hash]
      # @return [ResubmissionResult]
      def resubmit_trade(trade_id, original_form:)
        # TODO: Replace with actual API call
        ResubmissionResult.new(
          status: 'PERMITTED',
          validation_result: 'ACCEPTED'
        )
      end

      # Create document for RIB operations
      # @param broker: [Session]
      # @param terms: [Symbol] :capitalised, :standard
      # @return [Document]
      def create_document(broker:, terms: :standard, type: 'trade_confirmation')
        Document.new(
          id: "DOC_#{Time.now.to_i}",
          broker_id: broker.user_id,
          terms: terms,
          type: type
        )
      end

      # Process terminology from document
      # @param document [Document]
      # @return [TerminologyResult]
      def process_terminology(document)
        # TODO: Replace with actual API call
        TerminologyResult.new(
          compliance: document.terms_defined != false,
          source: 'LME Rulebook',
          status: document.terms_conflict ? 'rejected' : 'fulfilled'
        )
      end

      private

      def post(endpoint, body)
        # Placeholder for actual HTTP call
        # RestClient.post("#{@base_url}#{endpoint}", body.to_json, headers)
      end
    end

    # Value Objects

    class ValidationResult
      attr_reader :status, :errors, :rejection_reason, :compliant, :source

      def initialize(status: nil, errors: [], compliant: nil, source: nil, rejection_reason: nil)
        @status = status
        @errors = errors || []
        @compliant = compliant
        @source = source
        @rejection_reason = rejection_reason
      end

      def failed?
        @status == 'FAILED' || @errors.any?
      end

      def passed?
        !failed?
      end
    end

    class Document
      attr_reader :id, :broker_id, :type
      attr_accessor :terms, :terms_defined, :terms_conflict

      def initialize(id:, broker_id:, terms: :standard, type: 'trade_confirmation')
        @id = id
        @broker_id = broker_id
        @type = type
        @terms = terms
        @terms_defined = (terms != :undefined)
        @terms_conflict = false
      end

      def definitions=(value)
        @terms_defined = value
      end
    end

    class TradeSubmission
      attr_reader :id, :status, :params

      def initialize(id:, status:, params: {})
        @id = id
        @status = status
        @params = params
      end
    end

    class ResubmissionResult
      attr_reader :status, :validation_result

      def initialize(status:, validation_result:)
        @status = status
        @validation_result = validation_result
      end
    end

    class TerminologyResult
      attr_reader :compliance, :source, :status, :assignments

      def initialize(compliance:, source:, status:, assignments: nil)
        @compliance = compliance
        @source = source
        @status = status
        @assignments = assignments
      end
    end
  end
end
