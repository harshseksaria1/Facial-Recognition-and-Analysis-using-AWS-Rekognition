CREATE DATABASE customer_data;

USE customer_data;

CREATE TABLE logs
(
    logId       integer     NOT NULL PRIMARY KEY AUTO_INCREMENT,
    timest      timestamp,
    name        varchar(50) NULL,
    ageLow      integer,
    ageHigh     integer,
    gender      varchar(10),
    emotion     varchar(20),
    glassess    boolean,
    beard       boolean,
    preferences varchar(100),
    numPeople   integer
);

-- SETUP FOR VISUALIZATION

ALTER SCHEMA customer_data DEFAULT COLLATE utf8_bin; -- this will make sure new tables use utf8 instead of the default utf8mb4
ALTER TABLE customer_data.logs
    CONVERT TO CHARACTER SET UTF8MB3; -- coerce existing data back to utf8

SELECT *
FROM logs;


SELECT name, count(timest) timespent
FROM logs
WHERE name NOT IN ('')
GROUP BY name
ORDER BY timespent DESC;


SELECT name, emotion, count(timest)
FROM logs
GROUP BY name, emotion;