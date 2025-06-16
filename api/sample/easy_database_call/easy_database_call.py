def easy_database_call(
    url: str, username: str, password: str, sql: str, parameters: dict, config: dict
) -> dict:
    """
    Execute database query with direct driver support (synchronous version).

    Args:
        url: Database connection URL
        username: Database username
        password: Database password
        sql: SQL query (can be executed directly)
        parameters: Query parameters
        config: Tool configuration

    Returns:
        dict: Query results
    """
    from urllib.parse import urlparse

    print(f"url: {url}")
    print(f"username: {username}")
    print(f"sql: {sql}")

    try:
        # Parse database URL to determine driver type
        # Handle JDBC URL format: jdbc:mysql://host:port/database
        if url.startswith("jdbc:"):
            # Extract the actual database URL from JDBC format
            actual_url = url[5:]  # Remove 'jdbc:' prefix
            parsed_url = urlparse(actual_url)
        else:
            parsed_url = urlparse(url)

        scheme = parsed_url.scheme.lower()

        if scheme == "sqlite":
            # SQLite support (synchronous)
            import sqlite3

            db_path = parsed_url.path
            if db_path.startswith("/"):
                db_path = db_path[1:]  # Remove leading slash

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)

                # Get column names and descriptions
                columns = []
                if cursor.description:
                    for desc in cursor.description:
                        column_name = desc[0]
                        # SQLite doesn't provide column comments, use name as description
                        columns.append(
                            {"name": column_name, "description": column_name}
                        )

                # Fetch results
                rows = cursor.fetchall()

                # Convert to list of dicts
                results = []
                for row in rows:
                    result_dict = {}
                    for i, col_info in enumerate(columns):
                        result_dict[col_info["name"]] = row[i]
                    results.append(result_dict)

                return {"columns": columns, "rows": results, "row_count": len(results)}

        elif scheme in ["postgresql", "postgres"]:
            # PostgreSQL support (synchronous)
            import psycopg2
            import psycopg2.extras

            # Build connection string
            conn_str = f"postgresql://{username}:{password}@{parsed_url.hostname}:{parsed_url.port or 5432}{parsed_url.path}"

            with psycopg2.connect(conn_str) as conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cursor:
                    cursor.execute(sql)

                    # Get column names and descriptions
                    columns = []
                    if cursor.description:
                        for desc in cursor.description:
                            column_name = desc[0]
                            # PostgreSQL doesn't provide column comments in basic cursor, use name as description
                            columns.append(
                                {"name": column_name, "description": column_name}
                            )

                    # Fetch results
                    rows = cursor.fetchall()

                    # Convert to list of dicts
                    results = []
                    for row in rows:
                        results.append(dict(row))

                    return {
                        "columns": columns,
                        "rows": results,
                        "row_count": len(results),
                    }

        elif scheme == "mysql":
            # MySQL support (synchronous)
            import pymysql

            conn = pymysql.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 3306,
                user=username,
                password=password,
                database=parsed_url.path[1:] if parsed_url.path else None,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor,
            )
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql)

                    # Get column names and descriptions
                    columns = []
                    if cursor.description:
                        for desc in cursor.description:
                            column_name = desc[0]
                            # MySQL doesn't provide column comments in basic cursor, use name as description
                            columns.append(
                                {"name": column_name, "description": column_name}
                            )

                    # Fetch results
                    rows = cursor.fetchall()

                    # Convert to list of dicts (already dicts with DictCursor)
                    results = list(rows) if rows else []

                    return {
                        "columns": columns,
                        "rows": results,
                        "row_count": len(results),
                    }
            finally:
                conn.close()

        else:
            raise ValueError(f"Unsupported database scheme: {scheme}")

    except Exception as e:
        print(f"Error executing database query: {str(e)}")
        raise
