-- SET GLOBAL log_bin_trust_function_creators = 1;

DROP TABLE IF EXISTS `REVIEW`;
DROP TABLE IF EXISTS `ENTITY`;
DROP TABLE IF EXISTS `DIRECTOR`;
DROP TABLE IF EXISTS `MOVIE_CAST`;
DROP TABLE IF EXISTS `ACTOR`;
DROP TABLE IF EXISTS `USER`;
DROP TABLE IF EXISTS `MOVIE`;

CREATE TABLE `MOVIE` (
    `movie_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `release_year` YEAR DEFAULT NULL,
    `genre` VARCHAR(100) DEFAULT NULL,
    `rating` DECIMAL(3,1) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `tmdb_id` INT UNSIGNED DEFAULT NULL,
    UNIQUE KEY `uq_tmdb` (`tmdb_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ACTOR` (
    `actor_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(200) NOT NULL,
    `birthdate` DATE DEFAULT NULL,
    `country` VARCHAR(100) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `tmdb_id` INT UNSIGNED DEFAULT NULL,
    UNIQUE KEY `uq_tmdb` (`tmdb_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `USER` (
    `user_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password_hash` TEXT NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `MOVIE_CAST` (
    `cast_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `movie_id` INT UNSIGNED NOT NULL,
    `actor_id` INT UNSIGNED NOT NULL,
    `character_name` VARCHAR(255) DEFAULT NULL,
    `billing_order` SMALLINT UNSIGNED DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_cast_movie` (`movie_id`),
    INDEX `idx_cast_actor` (`actor_id`),
    CONSTRAINT `fk_cast_movie` FOREIGN KEY (`movie_id`) REFERENCES `MOVIE` (`movie_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_cast_actor` FOREIGN KEY (`actor_id`) REFERENCES `ACTOR` (`actor_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `uq_movie_actor` (`movie_id`,`actor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `DIRECTOR` (
    `director_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `movie_id` INT UNSIGNED NOT NULL,
    `actor_id` INT UNSIGNED NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_director_movie` (`movie_id`),
    INDEX `idx_director_actor` (`actor_id`),
    CONSTRAINT `fk_director_movie` FOREIGN KEY (`movie_id`) REFERENCES `MOVIE` (`movie_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_director_actor` FOREIGN KEY (`actor_id`) REFERENCES `ACTOR` (`actor_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `uq_movie_director` (`movie_id`, `actor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- unified entity table so a single (type,id) pair can be referenced by REVIEW
CREATE TABLE `ENTITY` (
    `entity_type` ENUM('MOVIE','ACTOR','MOVIE_CAST','DIRECTOR') NOT NULL,
    `entity_id` INT UNSIGNED NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`entity_type`,`entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- keep ENTITY in sync with base tables
CREATE TRIGGER `trg_movie_after_insert` AFTER INSERT ON `MOVIE` FOR EACH ROW
    INSERT IGNORE INTO `ENTITY` (`entity_type`,`entity_id`) VALUES ('MOVIE', NEW.movie_id);

CREATE TRIGGER `trg_movie_after_delete` AFTER DELETE ON `MOVIE` FOR EACH ROW
    DELETE FROM `ENTITY` WHERE `entity_type`='MOVIE' AND `entity_id`=OLD.movie_id;

CREATE TRIGGER `trg_actor_after_insert` AFTER INSERT ON `ACTOR` FOR EACH ROW
    INSERT IGNORE INTO `ENTITY` (`entity_type`,`entity_id`) VALUES ('ACTOR', NEW.actor_id);

CREATE TRIGGER `trg_actor_after_delete` AFTER DELETE ON `ACTOR` FOR EACH ROW
    DELETE FROM `ENTITY` WHERE `entity_type`='ACTOR' AND `entity_id`=OLD.actor_id;

CREATE TRIGGER `trg_cast_after_insert` AFTER INSERT ON `MOVIE_CAST` FOR EACH ROW
    INSERT IGNORE INTO `ENTITY` (`entity_type`,`entity_id`) VALUES ('MOVIE_CAST', NEW.cast_id);

CREATE TRIGGER `trg_cast_after_delete` AFTER DELETE ON `MOVIE_CAST` FOR EACH ROW
    DELETE FROM `ENTITY` WHERE `entity_type`='MOVIE_CAST' AND `entity_id`=OLD.cast_id;

CREATE TRIGGER `trg_director_after_insert` AFTER INSERT ON `DIRECTOR` FOR EACH ROW
    INSERT IGNORE INTO `ENTITY` (`entity_type`,`entity_id`) VALUES ('DIRECTOR', NEW.director_id);

CREATE TRIGGER `trg_director_after_delete` AFTER DELETE ON `DIRECTOR` FOR EACH ROW
    DELETE FROM `ENTITY` WHERE `entity_type`='DIRECTOR' AND `entity_id`=OLD.director_id;

-- REVIEW now references ENTITY with a single target_id + target_type
CREATE TABLE `REVIEW` (
    `review_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT UNSIGNED NOT NULL,
    `target_type` ENUM('MOVIE','ACTOR','MOVIE_CAST','DIRECTOR') NOT NULL,
    `target_id` INT UNSIGNED NOT NULL,
    `rating` DECIMAL(3,1) NOT NULL CHECK (`rating` >= 0 AND `rating` <= 10),
    `title` VARCHAR(255) DEFAULT NULL,
    `body` TEXT,
    `is_public` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_review_user` (`user_id`),
    INDEX `idx_review_target` (`target_type`,`target_id`),
    UNIQUE KEY `uq_user_target_type` (`user_id`,`target_type`,`target_id`),
    CONSTRAINT `fk_review_user` FOREIGN KEY (`user_id`) REFERENCES `USER` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_review_entity` FOREIGN KEY (`target_type`,`target_id`) REFERENCES `ENTITY` (`entity_type`,`entity_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
