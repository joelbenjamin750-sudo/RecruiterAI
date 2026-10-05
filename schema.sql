-- RecruiterAI Database Schema
-- Created on 2026-10-03

-- 1. Companies Table
CREATE TABLE Companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    website VARCHAR(255),
    contact_person VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users Table
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'recruiter',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Jobs Table
CREATE TABLE Jobs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(100),
    status VARCHAR(50) DEFAULT 'open', -- open, closed, on_hold
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Candidates Table
CREATE TABLE Candidates (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    resume_url TEXT,
    skills TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Applications Table
CREATE TABLE Applications (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES Jobs(id) ON DELETE CASCADE,
    candidate_id INTEGER REFERENCES Candidates(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'applied', -- applied, screened, interview, offered, hired, rejected
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, candidate_id) -- Prevent duplicate applications for same job
);

-- 6. Interview_Schedules Table
CREATE TABLE Interview_Schedules (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES Applications(id) ON DELETE CASCADE,
    interview_date DATE NOT NULL,
    interview_time TIME NOT NULL,
    type VARCHAR(50), -- Phone, Zoom, On-site, etc.
    interviewer_name VARCHAR(255),
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Followups Table
CREATE TABLE Followups (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES Applications(id) ON DELETE CASCADE,
    last_contact_date TIMESTAMP WITH TIME ZONE,
    next_contact_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed
    notes TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. AI_Analysis Table
CREATE TABLE AI_Analysis (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES Applications(id) ON DELETE CASCADE,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    summary TEXT,
    fit_reasoning TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
