
CREATE TABLE `MOVIE` (
    `movie_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `release_year` YEAR DEFAULT NULL,
    `genre` VARCHAR(100) DEFAULT NULL,
    `rating` DECIMAL(3,1) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ACTOR` (
    `actor_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(200) NOT NULL,
    `birthdate` DATE DEFAULT NULL,
    `country` VARCHAR(100) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `USER` (
    `user_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password_hash` TEXT NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `CAST` (
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

CREATE TABLE `REVIEW` (
    `review_id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT UNSIGNED NOT NULL,
    `movie_id` INT UNSIGNED DEFAULT NULL,
    `actor_id` INT UNSIGNED DEFAULT NULL,
    `cast_id` INT UNSIGNED DEFAULT NULL,
    `director_id` INT UNSIGNED DEFAULT NULL,
    `rating` DECIMAL(3,1) NOT NULL CHECK (`rating` >= 0 AND `rating` <= 10),
    `title` VARCHAR(255) DEFAULT NULL,
    `body` TEXT,
    `is_public` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- derived columns to enforce a single target and provide a stable key for uniqueness
    `target_type` ENUM('MOVIE','ACTOR','CAST','DIRECTOR') AS (
        CASE
            WHEN `movie_id` IS NOT NULL THEN 'MOVIE'
            WHEN `actor_id` IS NOT NULL THEN 'ACTOR'
            WHEN `cast_id` IS NOT NULL THEN 'CAST'
            WHEN `director_id` IS NOT NULL THEN 'DIRECTOR'
            ELSE NULL
        END
    ) STORED,
    `target_key` VARCHAR(64) AS (
        CASE
            WHEN `movie_id` IS NOT NULL THEN CONCAT('MOVIE_', `movie_id`)
            WHEN `actor_id` IS NOT NULL THEN CONCAT('ACTOR_', `actor_id`)
            WHEN `cast_id` IS NOT NULL THEN CONCAT('CAST_', `cast_id`)
            WHEN `director_id` IS NOT NULL THEN CONCAT('DIRECTOR_', `director_id`)
            ELSE NULL
        END
    ) STORED,
    INDEX `idx_review_user` (`user_id`),
    INDEX `idx_review_movie` (`movie_id`),
    INDEX `idx_review_actor` (`actor_id`),
    INDEX `idx_review_cast` (`cast_id`),
    INDEX `idx_review_director` (`director_id`),
    -- ensure exactly one target is specified
    CHECK (
        ( (`movie_id` IS NOT NULL) + (`actor_id` IS NOT NULL) + (`cast_id` IS NOT NULL) + (`director_id` IS NOT NULL) ) = 1
    ),
    -- prevent same user reviewing the same target more than once
    UNIQUE KEY `uq_user_target` (`user_id`, `target_key`),
    CONSTRAINT `fk_review_user` FOREIGN KEY (`user_id`) REFERENCES `USER` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_review_movie` FOREIGN KEY (`movie_id`) REFERENCES `MOVIE` (`movie_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_review_actor` FOREIGN KEY (`actor_id`) REFERENCES `ACTOR` (`actor_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_review_cast` FOREIGN KEY (`cast_id`) REFERENCES `CAST` (`cast_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_review_director` FOREIGN KEY (`director_id`) REFERENCES `DIRECTOR` (`director_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;