CREATE DATABASE IF NOT EXISTS `rfaddr_db` default charset utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `rfaddr_db`;
CREATE TABLE IF NOT EXISTS `rfaddr` (
 `rf_address` binary(3) NOT NULL,
 `st_uid_1` INT  NOT NULL,
 `st_uid_2` INT  NOT NULL,
 `st_uid_3` INT  NOT NULL,
 `operator` text COLLATE utf8mb4_unicode_ci NOT NULL,
 `status` TINYINT NOT NULL DEFAULT '0',
 UNIQUE KEY `rf_address` (`rf_address`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO 
	`rfaddr`(`rf_address`, `st_uid_1`, `st_uid_2`, `st_uid_3`, `operator`, `status`)
VALUES
	(0x002ba3,3014720,810438670,540620619,'yu',1),
	(0xa32b01,1572924,810438672,540620619,'yu',1);