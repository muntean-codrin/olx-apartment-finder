CREATE TABLE listings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50),
    title TEXT,
    date DATE,
    time TIME,
    location VARCHAR(255),
    price VARCHAR(50),
    link TEXT,
    reactualizat BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent INT
);