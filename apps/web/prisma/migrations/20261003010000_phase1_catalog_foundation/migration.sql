-- CreateTable
CREATE TABLE `comuni` (
    `id` SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `istat_code` CHAR(6) NOT NULL,
    `name` VARCHAR(120) NOT NULL,
    `province_code` CHAR(2) NOT NULL,
    `region` VARCHAR(40) NOT NULL,
    `postal_codes` JSON NOT NULL,
    `latitude` DECIMAL(9, 6) NOT NULL,
    `longitude` DECIMAL(9, 6) NOT NULL,

    UNIQUE INDEX `uq_comuni_istat`(`istat_code`),
    INDEX `idx_comuni_name`(`name`),
    INDEX `idx_comuni_province`(`province_code`),
    INDEX `idx_comuni_coords`(`latitude`, `longitude`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `users` (
    `id` CHAR(26) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `email_verified_at` DATETIME(3) NULL,
    `password_hash` VARCHAR(255) NULL,
    `full_name` VARCHAR(160) NOT NULL,
    `phone` VARCHAR(32) NULL,
    `locale` ENUM('it', 'en') NOT NULL DEFAULT 'it',
    `role` ENUM('adopter', 'shelter_staff', 'platform_admin') NOT NULL DEFAULT 'adopter',
    `status` ENUM('active', 'suspended', 'deleted') NOT NULL DEFAULT 'active',
    `marketing_opt_in` BOOLEAN NOT NULL DEFAULT false,
    `last_login_at` DATETIME(3) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `deleted_at` DATETIME(3) NULL,

    UNIQUE INDEX `uq_users_email`(`email`),
    INDEX `idx_users_role_status`(`role`, `status`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `shelters` (
    `id` CHAR(26) NOT NULL,
    `slug` VARCHAR(140) NOT NULL,
    `name` VARCHAR(160) NOT NULL,
    `legal_name` VARCHAR(200) NULL,
    `type` ENUM('canile_comunale', 'canile_privato', 'gattile', 'associazione', 'rifugio') NOT NULL,
    `tax_id` VARCHAR(20) NULL,
    `email` VARCHAR(255) NOT NULL,
    `phone` VARCHAR(32) NULL,
    `whatsapp_phone` VARCHAR(32) NULL,
    `website` VARCHAR(255) NULL,
    `social_links` JSON NULL,
    `address_line` VARCHAR(255) NOT NULL,
    `comune_id` SMALLINT UNSIGNED NOT NULL,
    `postal_code` CHAR(5) NOT NULL,
    `latitude` DECIMAL(9, 6) NULL,
    `longitude` DECIMAL(9, 6) NULL,
    `description_it` TEXT NULL,
    `description_en` TEXT NULL,
    `opening_hours` JSON NULL,
    `logo_key` VARCHAR(255) NULL,
    `cover_key` VARCHAR(255) NULL,
    `capacity_dogs` SMALLINT UNSIGNED NULL,
    `capacity_cats` SMALLINT UNSIGNED NULL,
    `status` ENUM('pending', 'active', 'suspended', 'archived') NOT NULL DEFAULT 'pending',
    `plan` ENUM('free', 'base', 'pro') NOT NULL DEFAULT 'free',
    `booking_cutoff_hours` SMALLINT UNSIGNED NOT NULL DEFAULT 24,
    `accepts_donations` BOOLEAN NOT NULL DEFAULT false,
    `approved_at` DATETIME(3) NULL,
    `approved_by` CHAR(26) NULL,
    `rejection_reason` TEXT NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `deleted_at` DATETIME(3) NULL,

    UNIQUE INDEX `uq_shelters_slug`(`slug`),
    INDEX `idx_shelters_status`(`status`),
    INDEX `idx_shelters_coords`(`latitude`, `longitude`),
    INDEX `idx_shelters_comune`(`comune_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `shelter_members` (
    `id` CHAR(26) NOT NULL,
    `shelter_id` CHAR(26) NOT NULL,
    `user_id` CHAR(26) NOT NULL,
    `is_billing_contact` BOOLEAN NOT NULL DEFAULT false,
    `invited_by` CHAR(26) NULL,
    `joined_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    INDEX `idx_member_user`(`user_id`),
    UNIQUE INDEX `uq_member`(`shelter_id`, `user_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `animals` (
    `id` CHAR(26) NOT NULL,
    `shelter_id` CHAR(26) NOT NULL,
    `slug` VARCHAR(160) NOT NULL,
    `internal_code` VARCHAR(40) NULL,
    `name` VARCHAR(80) NOT NULL,
    `species` ENUM('dog', 'cat') NOT NULL,
    `sex` ENUM('male', 'female', 'unknown') NOT NULL DEFAULT 'unknown',
    `size` ENUM('small', 'medium', 'large', 'xlarge') NULL,
    `breed_primary` VARCHAR(80) NULL,
    `breed_secondary` VARCHAR(80) NULL,
    `is_mixed` BOOLEAN NOT NULL DEFAULT true,
    `coat_color` VARCHAR(60) NULL,
    `coat_length` ENUM('short', 'medium', 'long') NULL,
    `birth_date` DATE NULL,
    `birth_date_estimated` BOOLEAN NOT NULL DEFAULT true,
    `weight_kg` DECIMAL(5, 2) NULL,
    `microchip_number` CHAR(15) NULL,
    `microchip_registered_on` DATE NULL,
    `anagrafe_region` VARCHAR(40) NULL,
    `is_sterilized` BOOLEAN NULL,
    `sterilized_on` DATE NULL,
    `has_special_needs` BOOLEAN NOT NULL DEFAULT false,
    `special_needs_summary` VARCHAR(255) NULL,
    `is_vaccinated_summary` BOOLEAN NULL,
    `headline_it` VARCHAR(140) NULL,
    `headline_en` VARCHAR(140) NULL,
    `story_it` TEXT NULL,
    `story_en` TEXT NULL,
    `adoption_fee_cents` INTEGER UNSIGNED NULL,
    `status` ENUM('draft', 'available', 'reserved', 'adopted', 'unavailable', 'transferred', 'deceased') NOT NULL DEFAULT 'draft',
    `unavailable_reason` ENUM('medical_hold', 'quarantine', 'behavioral_rehab', 'foster', 'other') NULL,
    `intake_date` DATE NOT NULL,
    `published_at` DATETIME(3) NULL,
    `adopted_at` DATETIME(3) NULL,
    `created_by` CHAR(26) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `deleted_at` DATETIME(3) NULL,

    UNIQUE INDEX `uq_animals_slug`(`slug`),
    UNIQUE INDEX `uq_animals_microchip`(`microchip_number`),
    INDEX `idx_animals_shelter_status`(`shelter_id`, `status`),
    INDEX `idx_animals_public`(`status`, `species`, `published_at`),
    INDEX `idx_animals_intake`(`intake_date`),
    FULLTEXT INDEX `ft_animals_text`(`name`, `breed_primary`, `story_it`, `story_en`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `animal_media` (
    `id` CHAR(26) NOT NULL,
    `animal_id` CHAR(26) NOT NULL,
    `kind` ENUM('photo', 'video') NOT NULL,
    `storage_key` VARCHAR(255) NOT NULL,
    `derivatives` JSON NULL,
    `placeholder` VARCHAR(512) NULL,
    `mime_type` VARCHAR(80) NOT NULL,
    `width` SMALLINT UNSIGNED NULL,
    `height` SMALLINT UNSIGNED NULL,
    `duration_seconds` SMALLINT UNSIGNED NULL,
    `byte_size` INTEGER UNSIGNED NOT NULL,
    `alt_text_it` VARCHAR(255) NULL,
    `alt_text_en` VARCHAR(255) NULL,
    `is_primary` BOOLEAN NOT NULL DEFAULT false,
    `sort_order` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    `processing_status` ENUM('pending', 'ready', 'failed') NOT NULL DEFAULT 'pending',
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `deleted_at` DATETIME(3) NULL,

    INDEX `idx_media_animal`(`animal_id`, `sort_order`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `animal_behavior_profiles` (
    `animal_id` CHAR(26) NOT NULL,
    `energy_level` TINYINT UNSIGNED NULL,
    `sociability_people` TINYINT UNSIGNED NULL,
    `good_with_children` ENUM('yes', 'older_only', 'no', 'unknown') NOT NULL DEFAULT 'unknown',
    `good_with_dogs` ENUM('yes', 'selective', 'no', 'unknown') NOT NULL DEFAULT 'unknown',
    `good_with_cats` ENUM('yes', 'selective', 'no', 'unknown') NOT NULL DEFAULT 'unknown',
    `house_trained` ENUM('yes', 'partially', 'no', 'unknown') NOT NULL DEFAULT 'unknown',
    `leash_trained` ENUM('yes', 'partially', 'no', 'unknown') NOT NULL DEFAULT 'unknown',
    `noise_tolerance` TINYINT UNSIGNED NULL,
    `alone_tolerance_hours` TINYINT UNSIGNED NULL,
    `training_needs` TINYINT UNSIGNED NULL,
    `grooming_needs` TINYINT UNSIGNED NULL,
    `exercise_min_per_day` SMALLINT UNSIGNED NULL,
    `suitable_for_first_time` ENUM('yes', 'no', 'unknown') NOT NULL DEFAULT 'unknown',
    `needs_garden` ENUM('yes', 'preferred', 'no', 'unknown') NOT NULL DEFAULT 'unknown',
    `temperament_tags` JSON NULL,
    `notes_it` TEXT NULL,
    `notes_en` TEXT NULL,
    `assessed_by` CHAR(26) NULL,
    `assessed_at` DATETIME(3) NULL,
    `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    PRIMARY KEY (`animal_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `shelters` ADD CONSTRAINT `shelters_comune_id_fkey` FOREIGN KEY (`comune_id`) REFERENCES `comuni`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `shelter_members` ADD CONSTRAINT `shelter_members_shelter_id_fkey` FOREIGN KEY (`shelter_id`) REFERENCES `shelters`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `shelter_members` ADD CONSTRAINT `shelter_members_user_id_fkey` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `animals` ADD CONSTRAINT `animals_shelter_id_fkey` FOREIGN KEY (`shelter_id`) REFERENCES `shelters`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `animal_media` ADD CONSTRAINT `animal_media_animal_id_fkey` FOREIGN KEY (`animal_id`) REFERENCES `animals`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE `animal_behavior_profiles` ADD CONSTRAINT `animal_behavior_profiles_animal_id_fkey` FOREIGN KEY (`animal_id`) REFERENCES `animals`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;
