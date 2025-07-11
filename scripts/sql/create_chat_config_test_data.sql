-- Create test data for chat configuration tables
-- Run this inside the backend container with psql

-- First, let's add some test chat strategies if they don't exist
INSERT INTO chat_strategies (id, name, description, system_prompt, is_active, created_at, updated_at)
VALUES 
    ('strategy-1', 'Genetic Counseling Assessment', 'Strategy for genetic counseling patient assessment', 'You are a genetic counseling assistant.', true, NOW(), NOW()),
    ('strategy-2', 'Oncology Screening', 'Strategy for oncology patient screening', 'You are an oncology screening assistant.', true, NOW(), NOW()),
    ('strategy-3', 'Cardiology Assessment', 'Strategy for cardiology risk assessment', 'You are a cardiology assessment assistant.', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Add some test knowledge sources if they don't exist
INSERT INTO knowledge_sources (id, name, description, file_path, content_type, processing_status, created_at, updated_at)
VALUES 
    ('ks-1', 'NCCN Guidelines', 'National Comprehensive Cancer Network Guidelines', '/docs/nccn_guidelines.pdf', 'application/pdf', 'processed', NOW(), NOW()),
    ('ks-2', 'ACOG Recommendations', 'American College of Obstetricians and Gynecologists recommendations', '/docs/acog_recommendations.pdf', 'application/pdf', 'processed', NOW(), NOW()),
    ('ks-3', 'AHA Heart Guidelines', 'American Heart Association guidelines', '/docs/aha_guidelines.pdf', 'application/pdf', 'processed', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Add targeting rules
INSERT INTO targeting_rules (id, strategy_id, field, operator, value, sequence, is_active, created_at)
VALUES 
    ('tr-1', 'strategy-1', 'appointment_type', 'is', '["genetic_counseling"]', 1, true, NOW()),
    ('tr-2', 'strategy-1', 'patient_age', 'is_between', '{"min": 18, "max": 65}', 2, true, NOW()),
    ('tr-3', 'strategy-2', 'appointment_type', 'is', '["oncology"]', 1, true, NOW()),
    ('tr-4', 'strategy-2', 'diagnosis', 'contains', '["cancer", "tumor", "oncology"]', 2, true, NOW()),
    ('tr-5', 'strategy-3', 'appointment_type', 'is', '["cardiology"]', 1, true, NOW())
ON CONFLICT (id) DO NOTHING;

-- Add outcome actions
INSERT INTO outcome_actions (id, strategy_id, condition, action_type, details, sequence, is_active, created_at)
VALUES 
    ('oa-1', 'strategy-1', 'meets_criteria', 'create_task', '{"task_type": "genetic_testing", "priority": "high", "assignee": "genetic_counselor"}', 1, true, NOW()),
    ('oa-2', 'strategy-1', 'does_not_meet_criteria', 'flag_chart', '{"flag_type": "low_risk", "color": "green"}', 2, true, NOW()),
    ('oa-3', 'strategy-2', 'meets_criteria', 'create_task', '{"task_type": "oncology_referral", "priority": "urgent", "assignee": "oncologist"}', 1, true, NOW()),
    ('oa-4', 'strategy-2', 'incomplete_data', 'send_message', '{"recipient": "primary_care", "message": "Additional information needed"}', 2, true, NOW()),
    ('oa-5', 'strategy-3', 'meets_criteria', 'schedule_followup', '{"appointment_type": "cardiology_followup", "timeframe": "2_weeks"}', 1, true, NOW())
ON CONFLICT (id) DO NOTHING;

-- Add strategy knowledge source associations
INSERT INTO strategy_knowledge_sources (id, strategy_id, knowledge_source_id, weight, is_active, created_at)
VALUES 
    ('sks-1', 'strategy-1', 'ks-2', 1.0, true, NOW()),
    ('sks-2', 'strategy-2', 'ks-1', 1.0, true, NOW()),
    ('sks-3', 'strategy-3', 'ks-3', 1.0, true, NOW()),
    ('sks-4', 'strategy-1', 'ks-1', 0.5, true, NOW())
ON CONFLICT (id) DO NOTHING;

-- Add strategy executions (some test executions)
INSERT INTO strategy_executions (id, strategy_id, session_id, patient_id, triggered_by, trigger_criteria, execution_status, outcome_result, executed_actions, started_at, completed_at, created_at)
VALUES 
    ('se-1', 'strategy-1', NULL, 'patient-1', 'admin-1', '{"appointment_type": "genetic_counseling", "age": 35}', 'completed', 'meets_criteria', '["create_task"]', NOW() - INTERVAL '1 day', NOW() - INTERVAL '23 hours', NOW() - INTERVAL '1 day'),
    ('se-2', 'strategy-2', NULL, 'patient-2', 'admin-1', '{"appointment_type": "oncology", "diagnosis": "breast cancer"}', 'completed', 'meets_criteria', '["create_task", "flag_chart"]', NOW() - INTERVAL '2 days', NOW() - INTERVAL '47 hours', NOW() - INTERVAL '2 days'),
    ('se-3', 'strategy-3', NULL, 'patient-3', 'admin-1', '{"appointment_type": "cardiology", "risk_factors": ["hypertension"]}', 'in_progress', NULL, '[]', NOW() - INTERVAL '6 hours', NULL, NOW() - INTERVAL '6 hours')
ON CONFLICT (id) DO NOTHING;

-- Add strategy analytics (sample data)
INSERT INTO strategy_analytics (id, strategy_id, date, patients_screened, criteria_met, criteria_not_met, incomplete_data, avg_duration_minutes, tasks_created, charts_flagged, messages_sent, followups_scheduled, created_at)
VALUES 
    ('sa-1', 'strategy-1', CURRENT_DATE - INTERVAL '1 day', 15, 8, 5, 2, 25, 8, 5, 2, 0, NOW()),
    ('sa-2', 'strategy-1', CURRENT_DATE, 12, 6, 4, 2, 23, 6, 4, 2, 1, NOW()),
    ('sa-3', 'strategy-2', CURRENT_DATE - INTERVAL '1 day', 20, 12, 6, 2, 18, 12, 8, 3, 2, NOW()),
    ('sa-4', 'strategy-2', CURRENT_DATE, 18, 10, 5, 3, 20, 10, 7, 2, 1, NOW()),
    ('sa-5', 'strategy-3', CURRENT_DATE - INTERVAL '1 day', 25, 15, 7, 3, 30, 15, 10, 5, 8, NOW()),
    ('sa-6', 'strategy-3', CURRENT_DATE, 22, 13, 6, 3, 28, 13, 9, 4, 6, NOW())
ON CONFLICT (strategy_id, date) DO NOTHING;

-- Display summary
SELECT 'Chat Strategies' as table_name, COUNT(*) as record_count FROM chat_strategies
UNION ALL
SELECT 'Knowledge Sources', COUNT(*) FROM knowledge_sources
UNION ALL
SELECT 'Targeting Rules', COUNT(*) FROM targeting_rules
UNION ALL
SELECT 'Outcome Actions', COUNT(*) FROM outcome_actions
UNION ALL
SELECT 'Strategy Knowledge Sources', COUNT(*) FROM strategy_knowledge_sources
UNION ALL
SELECT 'Strategy Executions', COUNT(*) FROM strategy_executions
UNION ALL
SELECT 'Strategy Analytics', COUNT(*) FROM strategy_analytics;
