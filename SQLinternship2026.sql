show databases;
use empinfo;
show tables;
select * from professinfo;
select * from professdep;
select * from professinfo where depid>(select avg(depid) from professinfo);
select * from professdep where salary<(select avg(salary) from professdep);
use college;
show tables;
select * from student;
drop table student;
show tables;
drop database college;
show databases;
use empinfo;
use flask_db;
show tables;
create database office;
create table emp(empid int primary key,name varchar(50),age int,loc varchar(100),depid int,sal int,gender varchar(10));
create table dep(depid int,depname varchar(50),floor int);
insert into emp(empid,name,age,loc,depid,sal,gender)values(1,'ram',19,'barabanki',01,10000,'m');
insert into emp(empid,name,age,loc,depid,sal,gender)values(2,'shweta',20,'barabanki',03,30000,'f');
insert into emp(empid,name,age,loc,depid,sal,gender)values(4,'sakshi',20,'lucknow',04,40000,'f');
-- Department Table Entries
INSERT INTO dep VALUES
(101, 'Human Resources', 1),
(102, 'Finance', 2),
(103, 'IT', 3),
(104, 'Marketing', 4),
(105, 'Operations', 5),
(106, 'Sales', 2),
(107, 'Research', 6),
(108, 'Legal', 3),
(109, 'Administration', 1),
(110, 'Customer Support', 4);
-- Employee Table Entries
INSERT INTO emp VALUES
(3, 'Rahul', 30, 'Kanpur', 101, 45000, 'Male'),
(5, 'Karan', 32, 'Gurugram', 105, 70000, 'Male'),
(6, 'Neha', 26, 'Jaipur', 106, 48000, 'Female'),
(7, 'Arjun', 29, 'Mumbai', 107, 75000, 'Male'),
(8, 'Sneha', 31, 'Pune', 108, 68000, 'Female'),
(9, 'Vikas', 35, 'Bhopal', 109, 52000, 'Male'),
(10, 'Anjali', 24, 'Chandigarh', 110, 46000, 'Female');
select * from emp;
select* from dep;
-- 1. Display all records from the Employee table
SELECT * FROM emp;

-- 2. Display only employee names and salaries
SELECT name, sal FROM emp;

-- 3. Display employee names along with their cities
SELECT name, loc FROM emp;

-- 4. Find employees whose salary is greater than 50000
SELECT * FROM emp WHERE sal > 50000;

-- 5. Find employees whose age is greater than 25
SELECT * FROM emp WHERE age > 25;

-- 6. Display all female employees
SELECT * FROM emp WHERE gender = 'Female';

-- 7. Display all employees who belong to Delhi
SELECT * FROM emp WHERE loc= 'Delhi';

-- 8. Find employees whose salary is between 40000 and 70000
SELECT * FROM emp WHERE sal BETWEEN 40000 AND 70000;

-- 9. Find employees whose names start with the letter 'A'
SELECT * FROM emp WHERE name LIKE 'A%';

-- 10. Find employees whose names end with the letter 'a'
SELECT * FROM emp WHERE name LIKE '%a';

-- 11. Display employees whose city is either Delhi or Mumbai
SELECT * FROM emp WHERE loc IN ('Delhi', 'Mumbai');

-- 12. Display employees whose salary is not equal to 50000
SELECT * FROM emp WHERE sal <> 50000;

-- 13. Sort employees based on salary in ascending order
SELECT * FROM emp ORDER BY sal ASC;

-- 14. Sort employees based on salary in descending order
SELECT * FROM emp ORDER BY sal DESC;

-- 15. Display the top 5 highest-paid employees
SELECT * FROM emp ORDER BY sal DESC LIMIT 5;
-- 1. Find the total number of employees
SELECT COUNT(*) AS total_employees FROM emp;

-- 2. Find the maximum salary among employees
SELECT MAX(sal) AS max_salary FROM emp;

-- 3. Find the minimum salary among employees
SELECT MIN(sal) AS min_salary FROM emp;

-- 4. Find the average salary of employees
SELECT AVG(sal) AS avg_salary FROM emp;

-- 5. Find the total salary paid by the company
SELECT SUM(sal) AS total_salary FROM emp;

-- 6. Find the total number of male employees
SELECT COUNT(*) AS male_count FROM emp WHERE gender = 'Male';

-- 7. Find the total number of female employees
SELECT COUNT(*) AS female_count FROM emp WHERE gender = 'Female';

-- 1. Display employee names along with their department names
SELECT e.name, d.depname
FROM emp e
JOIN dep d ON e.depid = d.depid;

-- 2. Display employee names with department locations
SELECT e.name, d.floor
FROM emp e
JOIN dep d ON e.depid = d.depid;

-- 3. Find all employees working in the IT department
SELECT e.*
FROM emp e
JOIN dep d ON e.depid = d.depid
WHERE d.depname = 'IT';

-- 4. Display all employees along with their department details
SELECT e.*, d.depname, d.floor
FROM emp e
JOIN dep d ON e.depid = d.depid;

-- 5. Display all departments along with employees (including departments with no employees)
SELECT e.name, d.depname, d.floor
FROM dep d
LEFT JOIN emp e ON e.depid = d.depid;

-- 6. Find employees who do not belong to any department
SELECT e.*
FROM emp e
LEFT JOIN dep d ON e.depid = d.depid
WHERE d.depid IS NULL;

-- 7. Display department-wise employee count using JOIN
SELECT d.depname, COUNT(e.empid) AS emp_count
FROM dep d
LEFT JOIN emp e ON e.depid = d.depid
GROUP BY d.depname;

-- 8. Find the highest salary employee in each department using JOIN
SELECT d.depname, e.name, e.sal
FROM emp e
JOIN dep d ON e.depid = d.depid
WHERE e.sal = (
    SELECT MAX(sal) FROM emp WHERE depid = d.depid
);

-- 9. Display employee name, salary, department name, and location
SELECT e.name, e.sal, d.depname, d.floor
FROM emp e
JOIN dep d ON e.depid = d.depid;

-- 10. Find employees working in departments located in Delhi
SELECT e.*
FROM emp e
JOIN dep d ON e.depid = d.depid
WHERE d.floor = 'Delhi';

-- 11. Find the total salary paid in each department using JOIN
SELECT d.depname, SUM(e.sal) AS total_salary
FROM dep d
JOIN emp e ON e.depid = d.depid
GROUP BY d.depname;

-- 12. Find departments having more than 5 employees using JOIN
SELECT d.depname, COUNT(e.empid) AS emp_count
FROM dep d
JOIN emp e ON e.depid = d.depid
GROUP BY d.depname
HAVING COUNT(e.empid) > 5;

-- 1. Find the department having the highest average salary
SELECT depid, AVG(sal) AS avg_salary
FROM emp
GROUP BY depid
ORDER BY avg_salary DESC
LIMIT 1;

-- 2. Find the department with the maximum number of employees
SELECT depid, COUNT(*) AS emp_count
FROM emp
GROUP BY depid
ORDER BY emp_count DESC
LIMIT 1;

-- 3. Find employees whose age is greater than the average age of all employees
SELECT *
FROM emp
WHERE age > (SELECT AVG(age) FROM emp);

-- 4. Find employees whose salary is above their department's average salary
SELECT e.*
FROM emp e
WHERE e.sal > (
    SELECT AVG(sal)
    FROM emp
    WHERE depid = e.depid
);
