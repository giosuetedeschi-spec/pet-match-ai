CREATE TABLE `adopter_profiles` (
    `id` CHAR(26) NOT NULL,
    `user_id` CHAR(26) NULL,
    `anonymous_token` CHAR(32) NULL,
    `housing_type` ENUM('apartment', 'house_no_garden', 'house_with_garden', 'farm') NULL,
    `housing_size_sqm` SMALLINT UNSIGNED NULL,
    `has_outdoor_space` BOOLEAN NULL,
    `outdoor_space_sqm` SMALLINT UNSIGNED NULL,
    `household_adults` TINYINT UNSIGNED NULL,
    `children_ages` JSON NULL,
    `existing_dogs` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `existing_cats` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `hours_alone_per_day` TINYINT UNSIGNED NULL,
    `activity_level` TINYINT UNSIGNED NULL,
    `experience_level` VARCHAR(20) NULL,
    `grooming_capacity` TINYINT UNSIGNED NULL,
    `training_capacity` TINYINT UNSIGNED NULL,
    `monthly_budget_eur` SMALLINT UNSIGNED NULL,
    `has_allergies` BOOLEAN NOT NULL DEFAULT false,
    `preferred_species` ENUM('dog', 'cat', 'either') NOT NULL DEFAULT 'either',
    `preferred_sizes` JSON NULL,
    `preferred_age_bands` JSON NULL,
    `preferred_sex` ENUM('male', 'female', 'any') NOT NULL DEFAULT 'any',
    `dealbreakers` JSON NULL,
    `search_comune_id` SMALLINT UNSIGNED NULL,
    `search_radius_km` SMALLINT UNSIGNED NOT NULL DEFAULT 50,
    `notify_new_matches` BOOLEAN NOT NULL DEFAULT false,
    `min_notify_score` TINYINT UNSIGNED NOT NULL DEFAULT 70,
    `is_active` BOOLEAN NOT NULL DEFAULT true,
    `current_step` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `completed_at` DATETIME(3) NULL,
    `last_match_digest_at` DATETIME(3) NULL,
    `last_match_computed_at` DATETIME(3) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    UNIQUE INDEX `uq_profile_user`(`user_id`),
    UNIQUE INDEX `uq_profile_anon`(`anonymous_token`),
    INDEX `idx_profile_active_notify`(`is_active`, `notify_new_matches`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `match_results` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `adopter_profile_id` CHAR(26) NOT NULL,
    `animal_id` CHAR(26) NOT NULL,
    `score` TINYINT UNSIGNED NOT NULL,
    `breakdown` JSON NOT NULL,
    `reasons` JSON NOT NULL,
    `considerations` JSON NULL,
    `explanation_it` VARCHAR(1000) NULL,
    `explanation_en` VARCHAR(1000) NULL,
    `engine_version` VARCHAR(20) NOT NULL,
    `computed_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `notified_at` DATETIME(3) NULL,

    UNIQUE INDEX `uq_match`(`adopter_profile_id`, `animal_id`),
    INDEX `idx_match_score`(`adopter_profile_id`, `score` DESC),
    INDEX `idx_match_notify`(`notified_at`, `score`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `favorites` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `adopter_profile_id` CHAR(26) NOT NULL,
    `animal_id` CHAR(26) NOT NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    UNIQUE INDEX `uq_favorite`(`adopter_profile_id`, `animal_id`),
    INDEX `idx_favorite_animal`(`animal_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `sessions` (
    `id` CHAR(26) NOT NULL,
    `user_id` CHAR(26) NOT NULL,
    `token_hash` CHAR(64) NOT NULL,
    `expires_at` DATETIME(3) NOT NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE INDEX `uq_sessions_token`(`token_hash`),
    INDEX `idx_sessions_user`(`user_id`),
    INDEX `idx_sessions_expiry`(`expires_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `verification_tokens` (
    `id` CHAR(26) NOT NULL,
    `user_id` CHAR(26) NOT NULL,
    `adopter_profile_id` CHAR(26) NULL,
    `token_hash` CHAR(64) NOT NULL,
    `purpose` ENUM('email_verification', 'password_reset') NOT NULL,
    `expires_at` DATETIME(3) NOT NULL,
    `consumed_at` DATETIME(3) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE INDEX `uq_verification_token`(`token_hash`),
    INDEX `idx_verification_user_expiry`(`user_id`, `purpose`, `expires_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `background_jobs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `type` VARCHAR(60) NOT NULL,
    `payload` JSON NOT NULL,
    `status` ENUM('queued', 'running', 'completed', 'failed') NOT NULL DEFAULT 'queued',
    `attempts` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `run_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `locked_at` DATETIME(3) NULL,
    `completed_at` DATETIME(3) NULL,
    `last_error` VARCHAR(500) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    INDEX `idx_background_jobs_ready`(`status`, `run_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `notifications` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` CHAR(26) NOT NULL,
    `type` VARCHAR(60) NOT NULL,
    `title_key` VARCHAR(120) NOT NULL,
    `payload` JSON NOT NULL,
    `link_url` VARCHAR(255) NULL,
    `read_at` DATETIME(3) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    INDEX `idx_notif_user_unread`(`user_id`, `read_at`, `created_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `notification_deliveries` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `notification_id` BIGINT UNSIGNED NOT NULL,
    `channel` VARCHAR(20) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `provider_message_id` VARCHAR(120) NULL,
    `error` VARCHAR(255) NULL,
    `attempts` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `sent_at` DATETIME(3) NULL,
    INDEX `idx_delivery_notification`(`notification_id`),
    INDEX `idx_delivery_retry`(`status`, `attempts`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `match_unsubscribe_tokens` (
    `id` CHAR(26) NOT NULL,
    `adopter_profile_id` CHAR(26) NOT NULL,
    `token_hash` CHAR(64) NOT NULL,
    `expires_at` DATETIME(3) NOT NULL,
    `consumed_at` DATETIME(3) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE INDEX `uq_match_unsubscribe_token`(`token_hash`),
    INDEX `idx_match_unsubscribe_profile`(`adopter_profile_id`, `expires_at`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE `adopter_profiles`
    ADD CONSTRAINT `adopter_profiles_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT `adopter_profiles_search_comune_id_fkey` FOREIGN KEY (`search_comune_id`) REFERENCES `comuni`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `match_results`
    ADD CONSTRAINT `match_results_adopter_profile_id_fkey` FOREIGN KEY (`adopter_profile_id`) REFERENCES `adopter_profiles`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT `match_results_animal_id_fkey` FOREIGN KEY (`animal_id`) REFERENCES `animals`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `favorites`
    ADD CONSTRAINT `favorites_adopter_profile_id_fkey` FOREIGN KEY (`adopter_profile_id`) REFERENCES `adopter_profiles`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT `favorites_animal_id_fkey` FOREIGN KEY (`animal_id`) REFERENCES `animals`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `sessions`
    ADD CONSTRAINT `sessions_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `verification_tokens`
    ADD CONSTRAINT `verification_tokens_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT `verification_tokens_adopter_profile_id_fkey` FOREIGN KEY (`adopter_profile_id`) REFERENCES `adopter_profiles`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `notifications`
    ADD CONSTRAINT `notifications_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `notification_deliveries`
    ADD CONSTRAINT `notification_deliveries_notification_id_fkey` FOREIGN KEY (`notification_id`) REFERENCES `notifications`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `match_unsubscribe_tokens`
    ADD CONSTRAINT `match_unsubscribe_tokens_adopter_profile_id_fkey` FOREIGN KEY (`adopter_profile_id`) REFERENCES `adopter_profiles`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;
