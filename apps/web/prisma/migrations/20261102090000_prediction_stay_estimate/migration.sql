ALTER TABLE `animal_predictions`
ADD COLUMN `estimated_days_if_adopted` DOUBLE NULL AFTER `adoption_probability`;
