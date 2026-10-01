-- Optional: the app creates this automatically (db.init_db), but you can run it by hand too.
CREATE DATABASE IF NOT EXISTS movieflix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE movieflix;
CREATE TABLE IF NOT EXISTS movies(
  id INT PRIMARY KEY, title VARCHAR(500), original_title VARCHAR(500), overview TEXT,
  release_date DATE NULL, vote_average DECIMAL(4,2), vote_count INT, popularity DECIMAL(12,3),
  poster_path VARCHAR(500), poster_url VARCHAR(1000), backdrop_path VARCHAR(500),
  backdrop_url VARCHAR(1000), genres VARCHAR(1000), keywords TEXT, language VARCHAR(20),
  adult BOOLEAN, INDEX idx_pop(popularity), INDEX idx_rel(release_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users(
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_username(username),
  INDEX idx_email(email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
