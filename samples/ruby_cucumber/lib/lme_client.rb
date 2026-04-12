# frozen_string_literal: true

# LME Client Library - Simulated API for testing
# This is a PROTOTYPE demonstrating the interface structure
# Replace with real API client implementation

module LME
  class Client
    class << self
      attr_accessor :base_url, :auth_token

      # Authenticate with LME trading platform
      # @param username [String]
      # @param password [String]
      # @return [Session] authenticated session
      def login(username:, password:)
        # TODO: Replace with actual API call
        # response = RestClient.post("#{base_url}/auth/login",
        #   { username: username, password: password })
        # Session.new(JSON.parse(response.body))

        # Prototype simulation
        Session.new(
          user_id: "user_#{username}",
          token: "token_#{Time.now.to_i}",
          member_id: "MEM_001"
        )
      end

      # Get broker session for RIB operations
      def registered_intermediary
        # Prototype - RIB-specific session
        Session.new(user_id: 'RIB_001', token: 'RIB_TOKEN', member_id: 'RIB_MEM')
      end

      # Get LME environment status
      def environment
        Environment.new(status: 'active', trading_date: Date.today)
      end

      # Get rulebook definition for a term
      # @param term [String]
      # @return [String] rulebook definition
      def get_rulebook_definition(term)
        # TODO: Replace with actual lookup
        RULES[term] || raise("Term not found in rulebook: #{term}")
      end
    end

    attr_reader :user_id, :token, :member_id

    def initialize(user_id:, token:, member_id: nil)
      @user_id = user_id
      @token = token
      @member_id = member_id || 'MEM_DEFAULT'
    end

    def broker_session
      self.class.registered_intermediary
    end
  end

  class Session
    attr_reader :user_id, :token, :member_id, :logged_in_at

    def initialize(user_id:, token:, member_id: nil)
      @user_id = user_id
      @token = token
      @member_id = member_id
      @logged_in_at = Time.now
    end

    def logged_in?
      Time.now - @logged_in_at < 3600 # 1 hour session
    end
  end

  class Environment
    attr_reader :status, :trading_date

    def initialize(status:, trading_date:)
      @status = status
      @trading_date = trading_date
    end

    def active?
      @status == 'active'
    end
  end

  # Sample rulebook definitions for prototype
  RULES = {
    'Capitalised terms' => 'terms defined in the Rules and Regulations of the LME',
    'Exchange' => 'London Metal Exchange (LME)',
    'Member' => 'authorised trading member of the LME',
    'Agreed Trade' => 'trade agreed subject to LME rules',
    'Prompt Date' => 'the date for delivery of metal',
    'Clearing House' => 'LME Clearing House Ltd'
  }.freeze
end
