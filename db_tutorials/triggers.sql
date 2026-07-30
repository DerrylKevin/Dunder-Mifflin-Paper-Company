-- =========================================
-- TABLE
-- =========================================
CREATE TABLE trigger_test (
    message VARCHAR(100)
);

-- =========================================
-- TRIGGER 1: log generic insert
-- =========================================

-- Function
CREATE OR REPLACE FUNCTION log_employee_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO trigger_test VALUES ('added new employee');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER my_trigger
BEFORE INSERT ON employee
FOR EACH ROW
EXECUTE FUNCTION log_employee_insert();

-- Test
INSERT INTO employee
VALUES (109, 'Oscar', 'Martinez', '1968-02-19', 'M', 69000, 106, 3);


-- =========================================
-- REPLACE TRIGGER (Postgres requires drop first)
-- =========================================
DROP TRIGGER my_trigger ON employee;

-- =========================================
-- TRIGGER 2: log first name
-- =========================================

-- Function
CREATE OR REPLACE FUNCTION log_employee_name()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO trigger_test VALUES (NEW.first_name);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER my_trigger
BEFORE INSERT ON employee
FOR EACH ROW
EXECUTE FUNCTION log_employee_name();

-- Test
INSERT INTO employee
VALUES (110, 'Kevin', 'Malone', '1978-02-19', 'M', 69000, 106, 3);


-- =========================================
-- REPLACE TRIGGER AGAIN
-- =========================================
DROP TRIGGER my_trigger ON employee;

-- =========================================
-- TRIGGER 3: conditional logic
-- =========================================

-- Function
CREATE OR REPLACE FUNCTION log_employee_by_gender()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.sex = 'M' THEN
        INSERT INTO trigger_test VALUES ('added male employee');
    ELSIF NEW.sex = 'F' THEN
        INSERT INTO trigger_test VALUES ('added female');
    ELSE
        INSERT INTO trigger_test VALUES ('added other employee');
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER my_trigger
BEFORE INSERT ON employee
FOR EACH ROW
EXECUTE FUNCTION log_employee_by_gender();

-- Test
INSERT INTO employee
VALUES (111, 'Pam', 'Beesly', '1988-02-19', 'F', 69000, 106, 3);


-- =========================================
-- CLEANUP (optional)
-- =========================================
DROP TRIGGER my_trigger ON employee;
DROP FUNCTION log_employee_insert;
DROP FUNCTION log_employee_name;
DROP FUNCTION log_employee_by_gender;