CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR UNIQUE NOT NULL,
    account_number VARCHAR UNIQUE NOT NULL,
    customer_name VARCHAR NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    account_type VARCHAR NOT NULL,
    current_balance BIGINT NOT NULL CHECK (current_balance >= 0),
    account_created_date DATE NOT NULL,
    home_location VARCHAR,
    account_status VARCHAR NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR UNIQUE NOT NULL,
    sender_account_id VARCHAR NOT NULL,
    sender_bank VARCHAR NOT NULL,
    receiver_account_id VARCHAR NOT NULL,
    receiver_bank VARCHAR NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0),
    transaction_timestamp TIMESTAMP NOT NULL,
    transaction_type VARCHAR NOT NULL,
    sender_balance_before BIGINT,
    sender_balance_after BIGINT,
    receiver_balance_before BIGINT,
    receiver_balance_after BIGINT,
    device_ip VARCHAR,        -- Format: "DeviceType:IPAddress" e.g. "Mobile:192.168.1.1"
    location VARCHAR,
    recipient_is_new BOOLEAN,
    transaction_status VARCHAR NOT NULL,
    honeypot_status VARCHAR DEFAULT 'NOT_TRANSFERRED',
    lien_status VARCHAR DEFAULT 'NO_LIEN',
    simulation_source VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_sender_receiver_diff CHECK (sender_account_id <> receiver_account_id)
);

CREATE INDEX IF NOT EXISTS idx_txn_sender ON transactions(sender_account_id);
CREATE INDEX IF NOT EXISTS idx_txn_receiver ON transactions(receiver_account_id);
CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(transaction_timestamp);
CREATE INDEX IF NOT EXISTS idx_txn_sender_ts ON transactions(sender_account_id, transaction_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_txn_receiver_ts ON transactions(receiver_account_id, transaction_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_acc_id ON accounts(account_id);
CREATE INDEX IF NOT EXISTS idx_acc_created ON accounts(account_id, account_created_date);

CREATE TABLE IF NOT EXISTS behaviour_history (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR NOT NULL,
    behaviour_date DATE NOT NULL,
    
    -- TRANSACTION VOLUME
    transaction_count INTEGER DEFAULT 0,
    sent_transaction_count INTEGER DEFAULT 0,
    received_transaction_count INTEGER DEFAULT 0,
    
    -- AMOUNT BEHAVIOUR
    total_amount_sent BIGINT DEFAULT 0,
    total_amount_received BIGINT DEFAULT 0,
    avg_transaction_amount BIGINT DEFAULT 0,
    min_transaction_amount BIGINT DEFAULT 0,
    max_transaction_amount BIGINT DEFAULT 0,
    
    -- COUNTERPARTY BEHAVIOUR
    unique_recipients INTEGER DEFAULT 0,
    unique_senders INTEGER DEFAULT 0,
    new_recipients_count INTEGER DEFAULT 0,
    new_senders_count INTEGER DEFAULT 0,
    
    -- VELOCITY
    transactions_1h INTEGER DEFAULT 0,
    transactions_6h INTEGER DEFAULT 0,
    transactions_24h INTEGER DEFAULT 0,
    avg_transaction_interval_seconds BIGINT DEFAULT 0,
    avg_transaction_interval_readable VARCHAR,
    min_transaction_interval_seconds BIGINT DEFAULT 0,
    min_transaction_interval_readable VARCHAR,
    
    -- TIME BEHAVIOUR
    first_transaction_time VARCHAR,
    last_transaction_time VARCHAR,
    active_hours INTEGER DEFAULT 0,
    night_transaction_count INTEGER DEFAULT 0,
    
    -- DEVICE BEHAVIOUR
    unique_device_count INTEGER DEFAULT 0,
    new_device_count INTEGER DEFAULT 0,
    device_change_count INTEGER DEFAULT 0,
    primary_device VARCHAR,   -- Most used device type that day e.g. "Mobile"
    
    -- LOCATION BEHAVIOUR
    unique_location_count INTEGER DEFAULT 0,
    new_location_count INTEGER DEFAULT 0,
    location_change_count INTEGER DEFAULT 0,
    
    -- MONEY-FLOW / MULE-LIKE FEATURES
    fan_in INTEGER DEFAULT 0,
    fan_out INTEGER DEFAULT 0,
    forwarded_amount BIGINT DEFAULT 0,
    same_day_forward_count INTEGER DEFAULT 0,
    short_dwell_count INTEGER DEFAULT 0,
    amount_split_count INTEGER DEFAULT 0,
    cross_bank_transaction_count INTEGER DEFAULT 0,
    
    -- BALANCE BEHAVIOUR
    opening_balance BIGINT DEFAULT 0,
    closing_balance BIGINT DEFAULT 0,
    min_balance BIGINT DEFAULT 0,
    max_balance BIGINT DEFAULT 0,
    avg_balance BIGINT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, behaviour_date)
);
