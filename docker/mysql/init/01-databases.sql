CREATE DATABASE IF NOT EXISTS petmatch_mvp
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

GRANT ALL PRIVILEGES ON petmatch_mvp.* TO 'petmatch'@'%';
