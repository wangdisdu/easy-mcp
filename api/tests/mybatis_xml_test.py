"""
Test cases for MyBatisXml class.
"""

import unittest
from api.mybatisx import MyBatisXml


class MyBatisXmlTest(unittest.TestCase):
    """Test cases for MyBatisXml class."""

    def test_simple_select(self):
        """Test simple SELECT statement."""
        sql_content = """
        SELECT
        id, username, email, created_at
        FROM users
        WHERE id = #{id}
        """
        mapper = MyBatisXml(sql_content)
        sql = mapper.get_sql({"id": 1})
        expected = "SELECT id, username, email, created_at FROM users WHERE id = 1"
        self.assertEqual(sql, expected)

    def test_if_condition(self):
        """Test IF condition."""
        sql_content = """
        SELECT
        id, username, email, created_at
        FROM users
        <where>
            1=1
            <if test="username != null">
                AND username LIKE CONCAT('%', #{username}, '%')
            </if>
            <if test="email != null">
                AND email = #{email}
            </if>
        </where>
        """
        mapper = MyBatisXml(sql_content)

        # Test with username
        sql = mapper.get_sql({"username": "john"})
        expected = "SELECT id, username, email, created_at FROM users WHERE username LIKE CONCAT('%', 'john', '%')"
        self.assertEqual(sql, expected)

        # Test with email
        sql = mapper.get_sql({"email": "john@example.com"})
        expected = "SELECT id, username, email, created_at FROM users WHERE email = 'john@example.com'"
        self.assertEqual(sql, expected)

        # Test with both
        sql = mapper.get_sql({"username": "john", "email": "john@example.com"})
        expected = "SELECT id, username, email, created_at FROM users WHERE username LIKE CONCAT('%', 'john', '%') AND email = 'john@example.com'"
        self.assertEqual(sql, expected)

    def test_trim_element(self):
        """Test TRIM element."""
        sql_content = """
        SELECT
        id, username, email, created_at
        FROM users
        <trim prefix="WHERE" prefixOverrides="AND |OR ">
            <if test="status != null">
                AND status = #{status}
            </if>
            <if test="keyword != null">
                AND (
                    username LIKE CONCAT('%', #{keyword}, '%')
                    OR email LIKE CONCAT('%', #{keyword}, '%')
                    OR created_by = #{keyword}
                    OR updated_by = #{keyword}
                )
            </if>
        </trim>
        """
        mapper = MyBatisXml(sql_content)

        # Test with status only
        sql = mapper.get_sql({"status": "active"})
        expected = (
            "SELECT id, username, email, created_at FROM users WHERE status = 'active'"
        )
        self.assertEqual(sql, expected)

        # Test with keyword only
        sql = mapper.get_sql({"keyword": "john"})
        expected = "SELECT id, username, email, created_at FROM users WHERE (username LIKE CONCAT('%', 'john', '%') OR email LIKE CONCAT('%', 'john', '%') OR created_by = 'john' OR updated_by = 'john')"
        self.assertEqual(sql, expected)

        # Test with both
        sql = mapper.get_sql({"status": "active", "keyword": "john"})
        expected = "SELECT id, username, email, created_at FROM users WHERE status = 'active' AND (username LIKE CONCAT('%', 'john', '%') OR email LIKE CONCAT('%', 'john', '%') OR created_by = 'john' OR updated_by = 'john')"
        self.assertEqual(sql, expected)

    def test_foreach_element(self):
        """Test FOREACH element."""
        sql_content = """
        DELETE FROM users
        WHERE id IN
        <foreach collection="ids" item="id" open="(" separator="," close=")">
            #{id}
        </foreach>
        """
        mapper = MyBatisXml(sql_content)
        sql = mapper.get_sql({"ids": [1, 2, 3]})
        expected = "DELETE FROM users WHERE id IN (1, 2, 3)"
        self.assertEqual(sql, expected)

    def test_choose_element(self):
        """Test CHOOSE element."""
        sql_content = """
        SELECT
        id, username, email, created_at
        FROM users
        <where>
            <choose>
                <when test="id != null">
                    AND id = #{id}
                </when>
                <when test="username != null">
                    AND username = #{username}
                </when>
                <otherwise>
                    AND status = 'active'
                </otherwise>
            </choose>
        </where>
        """
        mapper = MyBatisXml(sql_content)

        # Test with id
        sql = mapper.get_sql({"id": 1})
        expected = "SELECT id, username, email, created_at FROM users WHERE id = 1"
        self.assertEqual(sql, expected)

        # Test with username
        sql = mapper.get_sql({"username": "john"})
        expected = (
            "SELECT id, username, email, created_at FROM users WHERE username = 'john'"
        )
        self.assertEqual(sql, expected)

        # Test with neither (should use otherwise)
        sql = mapper.get_sql({})
        expected = (
            "SELECT id, username, email, created_at FROM users WHERE status = 'active'"
        )
        self.assertEqual(sql, expected)

    def test_set_element(self):
        """Test SET element."""
        sql_content = """
        UPDATE users
        <set>
            <if test="username != null">username = #{username},</if>
            <if test="email != null">email = #{email},</if>
        </set>
        WHERE id = #{id}
        """
        mapper = MyBatisXml(sql_content)
        sql = mapper.get_sql({"id": 1, "username": "john", "email": "john@example.com"})
        expected = "UPDATE users SET username = 'john', email = 'john@example.com' WHERE id = 1"
        self.assertEqual(sql, expected)

    def test_same_parameter_multiple_times(self):
        """Test same parameter used multiple times."""
        sql_content = """
        SELECT
        id, username, email, created_at
        FROM users
        WHERE (username = #{keyword} OR email = #{keyword})
        AND status = 'active'
        AND (created_by = #{keyword} OR updated_by = #{keyword})
        """
        mapper = MyBatisXml(sql_content)
        sql = mapper.get_sql({"keyword": "john"})
        expected = (
            "SELECT id, username, email, created_at FROM users "
            "WHERE (username = 'john' OR email = 'john') "
            "AND status = 'active' "
            "AND (created_by = 'john' OR updated_by = 'john')"
        )
        self.assertEqual(sql, expected)


if __name__ == "__main__":
    unittest.main()
