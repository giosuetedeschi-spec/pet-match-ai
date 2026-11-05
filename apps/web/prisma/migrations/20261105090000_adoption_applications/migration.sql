CREATE TABLE `adoption_applications` (
  `id` CHAR(26) NOT NULL,
  `adopter_id` CHAR(26) NOT NULL,
  `animal_id` CHAR(26) NOT NULL,
  `status` ENUM('submitted', 'in_review', 'home_visit', 'approved', 'rejected', 'withdrawn') NOT NULL DEFAULT 'submitted',
  `motivational_notes` TEXT NOT NULL,
  `shelter_notes` TEXT NULL,
  `submitted_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uq_application_adopter_animal` (`adopter_id`, `animal_id`),
  INDEX `idx_application_animal_status` (`animal_id`, `status`, `submitted_at`),
  INDEX `idx_application_adopter_date` (`adopter_id`, `submitted_at`),
  CONSTRAINT `fk_application_adopter` FOREIGN KEY (`adopter_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_application_animal` FOREIGN KEY (`animal_id`) REFERENCES `animals` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE `home_visits` (
  `id` CHAR(26) NOT NULL,
  `application_id` CHAR(26) NOT NULL,
  `evaluator_name` VARCHAR(150) NOT NULL,
  `scheduled_at` DATETIME(3) NOT NULL,
  `outcome` ENUM('pending', 'passed', 'failed') NOT NULL DEFAULT 'pending',
  `report_notes` TEXT NOT NULL,
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uq_home_visit_application` (`application_id`),
  CONSTRAINT `fk_home_visit_application` FOREIGN KEY (`application_id`) REFERENCES `adoption_applications` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
