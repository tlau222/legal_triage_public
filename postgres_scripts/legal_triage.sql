CREATE TABLE IF NOT EXISTS business_legal (
    business_issue_id SERIAL PRIMARY KEY ,
    business_issue varchar(255) NOT NULL,
    business_issue_stemmed varchar(255) NOT NULL,
    legal_issue varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS legal_issues (
    legal_issue_id SERIAL PRIMARY KEY ,
    legal_issue varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS professional_legal (
    professional_legal_id SERIAL PRIMARY KEY ,
    legal_id int NOT NULL,
    legal_professional_id int NOT NULL
);

CREATE TABLE IF NOT EXISTS legal_professional_info (
    legal_professional_id SERIAL PRIMARY KEY,
    first_name varchar(255) NOT NULL,
    last_name varchar(255) NOT NULL,
    title varchar(255) NOT NULL,
    legal_department varchar(255),
    email varchar(255) NOT NULL,
    phone_number varchar(255) NOT NULL
);

-- inserting unique legal issues into legal_issue
INSERT INTO legal_issues (legal_issue)
SELECT DISTINCT legal_issue
FROM business_legal_raw;

-- inserting business issues, stemmed business issues, and legal issues into business_legal_raw
INSERT INTO business_legal (business_issue, business_issue_stemmed, legal_issue)
SELECT business_issue, stemmed_issue, legal_issue
FROM business_legal_raw;

-- linking legal issue with legal professional
SELECT DISTINCT (SELECT legal_issue_id FROM legal_issues li WHERE li.legal_issue = business_legal_raw.legal_issue)
    ,(SELECT legal_professional_id FROM legal_professional_info lpi WHERE (lpi.first_name || ' ' || lpi.last_name) = business_legal_raw.legal_professional)
FROM business_legal_raw;

-- inserting legal issue and legal professional into professional_legal
INSERT INTO professional_legal (legal_id, legal_professional_id)
SELECT DISTINCT (SELECT legal_issue_id FROM legal_issues li WHERE li.legal_issue = business_legal_raw.legal_issue)
    ,(SELECT legal_professional_id FROM legal_professional_info lpi WHERE (lpi.first_name || ' ' || lpi.last_name) = business_legal_raw.legal_professional)
FROM business_legal_raw;

----------------------------------------------------------------
-- Search Functionality
-- use pg_trgm package
CREATE EXTENSION pg_trgm;
CREATE EXTENSION btree_gist;
CREATE INDEX ON business_legal USING GIST (business_issue_stemmed gist_trgm_ops, business_issue_id);

SELECT set_limit(0.3);

-- CREATE FUNCTION filtered_issues_table()
-- RETURNS TABLE (legal_issue varchar(255), similarity float8) LANGUAGE plpgsql AS
-- $$
--     DECLARE filtered_issues business_legal;
--     BEGIN
--         RETURN QUERY
--         SELECT business_legal.legal_issue
--             ,similarity(business_issue_stemmed, 'presentation review') AS similarity
--         INTO
--             filtered_issues
--         FROM business_legal
--         WHERE business_issue_stemmed % 'presentation review';
--     END;
-- $$;

-- DROP TABLE IF EXISTS filtered_issues;
-- CREATE TEMP TABLE filtered_issues (
--     legal_issue varchar(255),
--     similarity float8
-- );
--
-- -- drop table filtered_issues;
--
-- SELECT legal_issue
--     ,similarity(business_issue_stemmed, 'presentation review') AS similarity
-- INTO
--     filtered_issues
-- FROM business_legal
-- WHERE business_issue_stemmed % 'presentation review';
--
-- CREATE TEMP TABLE filtered_legal_issue_id (
--     legal_issue_id int,
--     similarity float8
-- );
--
-- drop table filtered_legal_issue_id;
--
-- SELECT li.legal_issue,
--        li.legal_issue_id
--     ,similarity
-- INTO
--     filtered_legal_issue_id
-- FROM
--     filtered_issues
-- JOIN legal_issues li ON li.legal_issue = filtered_issues.legal_issue;

-- select * from filtered_issues_table();

SELECT DISTINCT ON (lawyer_info.lawyer_id)
        lawyer_info.lawyer_id,
       (first_name || ' ' || last_name) AS name,
       title,
       email,
       phone_number,
       legal_department,
       (SELECT
               string_agg(issue, ', ')
       FROM
            (SELECT DISTINCT
                             i2.issue
            FROM
                 lawyer_issue li2,
                 issue_problem i2
            WHERE li2.lawyer_id = filtered_id.lawyer_id
              AND i2.issue_id = li2.issue_id) issues) issue,
        similarity
FROM lawyer_info,
     (SELECT DISTINCT legal_issue_id,
                      similarity
      FROM legal_issues,
     (SELECT legal_issue
           ,similarity(business_issue_stemmed, 'presentation review') AS similarity
     FROM business_legal
     WHERE business_issue_stemmed % 'presentation review')AS filtered_issues
     WHERE legal_issues.legal_issue = filtered_issues.legal_issue) AS filtered_id
WHERE lawyer_info.lawyer_id = filtered_id.lawyer_id
ORDER BY
         lawyer_info.lawyer_id,
         similarity DESC;

-- lookup the related legal issues
SELECT legal_issue
    ,similarity(business_issue_stemmed, 'presentation review') AS similarity
FROM business_legal
WHERE business_issue_stemmed % 'presentation review'
ORDER BY similarity DESC;

SELECT legal_issue
    ,similarity(business_issue_stemmed, 'contract') AS similarity
    ,business_issue_id
FROM business_legal
WHERE business_issue_stemmed % 'contract'
ORDER BY similarity DESC;

-- find legal issue id
SELECT DISTINCT legal_issue_id
--     ,filtered_legal_issues.legal_issue
    ,similarity
FROM legal_issues, filtered_legal_issues
WHERE filtered_legal_issues.legal_issue = legal_issues.legal_issue;

-- find the legal professional linked to the legal issue
SELECT DISTINCT legal_professional_id
    ,similarity
FROM professional_legal, filtered_legal_ids
WHERE filtered_legal_ids.legal_issue_id = professional_legal.legal_issue_id
ORDER BY similarity DESC;

-- find lawyer information from filtered legal professional ids
SELECT DISTINCT ON (legal_professional_info.legal_professional_id) legal_professional_info.legal_professional_id
    ,(first_name || ' ' || last_name) AS name
    ,title
    ,legal_department
    ,email
    ,phone_number
    ,similarity
FROM legal_professional_info, filtered_legal_professional_ids
WHERE filtered_legal_professional_ids.legal_professional_id = legal_professional_info.legal_professional_id;

-- list out legal issues handled by legal professional
CREATE TABLE professional_issues AS
SELECT DISTINCT (first_name || ' ' || last_name) legal_professional
    ,legal_issue
FROM professional_legal
    ,legal_professional_info
    ,legal_issues
WHERE legal_issues.legal_issue_id = professional_legal.legal_issue_id
AND legal_professional_info.legal_professional_id = professional_legal.legal_professional_id;

CREATE TABLE professional_issues_list AS
SELECT legal_professional,
       string_agg(legal_issue, ', ' ORDER BY legal_professional) legal_issue_list
FROM professional_issues
GROUP BY legal_professional
ORDER BY legal_professional;

SELECT name
    ,title
    ,legal_department
    ,email
    ,phone_number
    ,similarity
    ,legal_issue_list
FROM final_legal_professionals
JOIN professional_issues_list ON professional_issues_list.legal_professional = final_legal_professionals.name
ORDER BY similarity DESC;

select * from final_legal_professionals;

CREATE TABLE legal_issues_names AS
SELECT DISTINCT legal_professional_id
    ,filtered_legal_ids.legal_issue_id
FROM professional_legal, filtered_legal_ids
WHERE filtered_legal_ids.legal_issue_id = professional_legal.legal_issue_id;

SELECT (first_name || ' ' || last_name) AS name
    ,legal_issue
FROM legal_professional_info
    ,legal_issues
    ,legal_issues_names
WHERE legal_issues_names.legal_professional_id = legal_professional_info.legal_professional_id
AND legal_issues.legal_issue_id = legal_issues_names.legal_issue_id;

----------------------------------------------------------------
-- Adding Data
-- inserting new business issue
INSERT INTO business_legal (business_issue, business_issue_stemmed, legal_issue) VALUES ('business 1', 'busi 1', 'legal 1');

-- inserting new legal issue
SELECT legal_issue_id
FROM legal_issues
WHERE legal_issues.legal_issue = 'Contracts';

-- find legal professional id
SELECT legal_professional_id
FROM legal_professional_info
WHERE (first_name || ' ' || last_name) = 'Alaaeddine Sahibi';

-- inserting legal issue linked with legal professional
INSERT INTO professional_legal (legal_id, legal_professional_id) VALUES (3, 28);

