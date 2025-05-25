-- MySQL initialization script for Easy MCP
-- This script is executed when the MySQL container starts for the first time

-- Set timezone
SET time_zone = '+00:00';

-- Set character set and collation
ALTER DATABASE easy_mcp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON easy_mcp.* TO 'easy_mcp'@'%';
FLUSH PRIVILEGES;

-- Set SQL mode for better compatibility
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Log initialization
SELECT 'MySQL database initialized for Easy MCP' AS message;
