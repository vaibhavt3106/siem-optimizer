-- Drop existing rules if needed (optional, be careful in prod!)
-- TRUNCATE rules CASCADE;

INSERT INTO rules (id, name, query, source, created_at, updated_at) VALUES
('Block_Brute_Force', 'Block Brute Force',
 'index=auth action=failure | stats count by user',
 'Splunk', NOW(), NOW()),
('Rare_Process_Spawn', 'Rare Process Spawn',
 'index=proc parent=cmd.exe | stats count by process_name',
 'Splunk', NOW(), NOW()),
('DNS_Anomaly', 'DNS Anomaly Detection',
 'index=dns | stats count by query_name | where count > 100',
 'Splunk', NOW(), NOW()),
('Suspicious_Powershell', 'Suspicious PowerShell Execution',
 'index=proc process_name=powershell.exe | stats count by user, host',
 'Splunk', NOW(), NOW()),
('Multiple_Failed_Logins', 'Multiple Failed Logins',
 'index=auth action=failure earliest=-1h latest=now | stats count by user | where count > 10',
 'Splunk', NOW(), NOW())
ON CONFLICT (id) DO UPDATE 
SET name = EXCLUDED.name,
    query = EXCLUDED.query,
    source = EXCLUDED.source,
    updated_at = NOW();
