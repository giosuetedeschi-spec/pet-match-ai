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

ALTER TABLE `adopter_profiles`
    ADD CONSTRAINT `adopter_profiles_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT `adopter_profiles_search_comune_id_fkey` FOREIGN KEY (`search_comune_id`) REFERENCES `comuni`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `match_results`
    ADD CONSTRAINT `match_results_adopter_profile_id_fkey` FOREIGN KEY (`adopter_profile_id`) REFERENCES `adopter_profiles`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT `match_results_animal_id_fkey` FOREIGN KEY (`animal_id`) REFERENCES `animals`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `favorites`
    ADD CONSTRAINT `favorites_adopter_profile_id_fkey` FOREIGN KEY (`adopter_profile_id`) REFERENCES `adopter_profiles`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT `favorites_animal_id_fkey` FOREIGN KEY (`animal_id`) REFERENCES `animals`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;
