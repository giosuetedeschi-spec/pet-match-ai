CREATE TABLE `animal_predictions` (
    `id` CHAR(26) NOT NULL,
    `animal_id` CHAR(26) NOT NULL,
    `model_version` VARCHAR(80) NOT NULL,
    `mode` VARCHAR(20) NOT NULL,
    `predicted_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `adoption_probability` DOUBLE NOT NULL,
    `bucket_probabilities` JSON NOT NULL,
    `top_factors` JSON NOT NULL,
    `data_completeness` DOUBLE NOT NULL,
    INDEX `idx_prediction_animal_date` (`animal_id`, `predicted_at`),
    PRIMARY KEY (`id`),
    CONSTRAINT `animal_predictions_animal_id_fkey` FOREIGN KEY (`animal_id`) REFERENCES `animals` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
