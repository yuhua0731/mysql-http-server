-- run with "mysql -u username -p -t < path/to/script.sql"
-- -t: get the "table-like" output
-- -vvv: echo the input commands

-- Hex values are written as 0x.... or X'....' or x'....'
CREATE DATABASE IF NOT EXISTS test;     -- Create database
SHOW WARNINGS;
SHOW DATABASES;                         -- List the name of all the databases in this server
USE test;                               -- Set system database 'mysql' as the current database
CREATE TABLE IF NOT EXISTS rfaddr (
 `rf_address` binary(3) NOT NULL,
 `st_uid` binary(12) NOT NULL,
 `operator` text COLLATE utf8_bin NOT NULL,
 `status` tinyint(1) NOT NULL DEFAULT '0',
 UNIQUE KEY `rf_address` (`rf_address`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;     -- Create table
SHOW WARNINGS;
SELECT * FROM rfaddr;                  -- List all users by querying table 'user'