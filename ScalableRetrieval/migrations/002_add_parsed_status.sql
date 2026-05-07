DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_status') THEN
        ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'parsed';
    END IF;
END $$;
