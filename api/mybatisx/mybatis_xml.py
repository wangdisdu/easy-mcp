"""
MyBatis XML parser and SQL generator.
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional


class MyBatisXml:
    """
    MyBatis XML parser and SQL generator.

    This class provides functionality to parse MyBatis XML SQL fragments and generate
    executable SQL statements with parameter substitution.
    """

    def __init__(self, sql_content: str):
        """
        Initialize MyBatisXml with SQL content.

        Args:
            sql_content: MyBatis SQL content (without mapper wrapper)
        """
        self.sql_content = sql_content
        # Wrap the SQL content in a temporary root element for parsing
        wrapped_content = f"<root>{sql_content}</root>"
        self.root = ET.fromstring(wrapped_content)

    def _substitute_parameters(self, sql: str, params: Dict[str, Any]) -> str:
        """
        Substitute parameters in SQL text.

        Args:
            sql: SQL text with parameter placeholders
            params: Parameter dictionary

        Returns:
            str: SQL text with substituted parameters
        """
        # 如果有任何参数为 None，直接返回空字符串
        for match in re.finditer(r"#\{(\w+)\}", sql):
            key = match.group(1)
            if params.get(key, None) is None:
                return ""

        def replacer(match):
            key = match.group(1)
            value = params.get(key, None)
            # 检查参数是否在 CONCAT 函数内部
            before = sql[max(0, match.start() - 20) : match.start()]
            after = sql[match.end() : match.end() + 10]

            if isinstance(value, str):
                # 如果在 CONCAT 函数内部，需要加引号
                if "CONCAT(" in before and ")" in after:
                    return f"'{value}'"
                # 如果在 IN 子句中，不加引号
                elif "IN" in before and ("(" in before or "(" in after):
                    return value
                # 其他字符串情况加引号
                else:
                    return f"'{value}'"
            else:
                return str(value)

        return re.sub(r"#\{(\w+)\}", replacer, sql)

    def _get_sql_text(self, element: ET.Element) -> str:
        """
        Get the SQL text from an element, handling nested elements.

        Args:
            element: XML element

        Returns:
            str: SQL text
        """
        text = element.text or ""
        for child in element:
            text += self._get_sql_text(child)
            text += child.tail or ""
        return text.strip()

    def _process_if(self, element: ET.Element, params: Dict[str, Any]) -> str:
        test = element.get("test", "")
        if self._evaluate_condition(test, params):
            text = element.text or ""
            for child in element:
                text += self._process_element(child, params)
                text += child.tail or ""
            return text
        return ""

    def _process_foreach(self, element: ET.Element, params: Dict[str, Any]) -> str:
        collection = element.get("collection", "")
        item = element.get("item", "")
        separator = element.get("separator", ",")
        open_str = element.get("open", "")
        close_str = element.get("close", "")

        if collection not in params:
            return ""
        items = params[collection]
        if not isinstance(items, (list, tuple)):
            return ""
        result = []
        for value in items:
            temp_params = params.copy()
            temp_params[item] = value
            sql = element.text or ""
            for child in element:
                sql += self._process_element(child, temp_params)
                sql += child.tail or ""
            sql = self._substitute_parameters(sql.strip(), temp_params)
            result.append(sql)
        if not result:
            return ""
        return f"{open_str}{separator.join(result)}{close_str}".replace(",", ", ")

    def _process_choose(self, element: ET.Element, params: Dict[str, Any]) -> str:
        for when in element.findall("when"):
            test = when.get("test", "")
            if self._evaluate_condition(test, params):
                text = when.text or ""
                for child in when:
                    text += self._process_element(child, params)
                    text += child.tail or ""
                return text
        otherwise = element.find("otherwise")
        if otherwise is not None:
            text = otherwise.text or ""
            for child in otherwise:
                text += self._process_element(child, params)
                text += child.tail or ""
            return text
        return ""

    def _process_where(self, element: ET.Element, params: Dict[str, Any]) -> str:
        text = ""
        for child in element:
            part = self._process_element(child, params)
            if part.strip():
                text += part
                text += child.tail or ""
        sql = text.strip()
        if not sql:
            return ""
        sql = re.sub(r"^\s*(AND|OR)\s+", "", sql, flags=re.IGNORECASE)
        sql = self._substitute_parameters(sql, params)
        if not sql:
            return ""
        return f"WHERE {sql}"

    def _process_set(self, element: ET.Element, params: Dict[str, Any]) -> str:
        text = ""
        for child in element:
            part = self._process_element(child, params)
            if part.strip():
                text += part
                text += child.tail or ""
        sql = text.strip()
        if not sql:
            return ""
        sql = re.sub(r"^\s*,\s*|\s*,\s*$", "", sql)
        sql = self._substitute_parameters(sql, params)
        if not sql:
            return ""
        return f"SET {sql}"

    def _process_trim(self, element: ET.Element, params: Dict[str, Any]) -> str:
        prefix = element.get("prefix", "")
        suffix = element.get("suffix", "")
        prefix_overrides = element.get("prefixOverrides", "").split("|")
        suffix_overrides = element.get("suffixOverrides", "").split("|")
        text = ""
        for child in element:
            part = self._process_element(child, params)
            if part.strip():
                text += part
                text += child.tail or ""
        sql = text.strip()
        if not sql:
            return ""
        sql = re.sub(r"^(AND|OR)\s+", "", sql, flags=re.IGNORECASE)
        for override in prefix_overrides:
            if override:
                sql = re.sub(f"^{override}\\s+", "", sql, flags=re.IGNORECASE)
        for override in suffix_overrides:
            if override:
                sql = re.sub(f"\\s+{override}$", "", sql, flags=re.IGNORECASE)
        sql = self._substitute_parameters(sql, params)
        if not sql:
            return ""
        if prefix and suffix:
            return f"{prefix} {sql} {suffix}".strip()
        elif prefix:
            return f"{prefix} {sql}".strip()
        elif suffix:
            return f"{sql} {suffix}".strip()
        else:
            return sql

    def _process_bind(self, element: ET.Element, params: Dict[str, Any]) -> str:
        """
        Process bind elements by creating new parameters.

        Args:
            element: XML element containing bind
            params: Parameter dictionary

        Returns:
            str: Empty string (bind only affects parameters)
        """
        name = element.get("name")
        value = element.get("value")
        if name and value:
            # Evaluate the value expression
            try:
                # Replace parameter references with their values
                for param_name, param_value in params.items():
                    value = value.replace(f"#{param_name}", str(param_value))
                params[name] = value
            except Exception:
                pass
        return ""

    def _process_element(self, element: ET.Element, params: Dict[str, Any]) -> str:
        # Handle special elements first
        if element.tag == "if":
            return self._process_if(element, params)
        elif element.tag == "foreach":
            return self._process_foreach(element, params)
        elif element.tag == "choose":
            return self._process_choose(element, params)
        elif element.tag == "where":
            return self._process_where(element, params)
        elif element.tag == "set":
            return self._process_set(element, params)
        elif element.tag == "trim":
            return self._process_trim(element, params)
        elif element.tag == "bind":
            return self._process_bind(element, params)

        # Handle generic elements
        text = element.text or ""
        for child in element:
            part = ""
            if child.tag == "if":
                part = self._process_if(child, params)
            elif child.tag == "foreach":
                part = self._process_foreach(child, params)
            elif child.tag == "choose":
                part = self._process_choose(child, params)
            elif child.tag == "where":
                part = self._process_where(child, params)
            elif child.tag == "set":
                part = self._process_set(child, params)
            elif child.tag == "trim":
                part = self._process_trim(child, params)
            elif child.tag == "bind":
                part = self._process_bind(child, params)
            else:
                part = self._process_element(child, params)
            if part.strip():
                text += part
                text += child.tail or ""
        return self._substitute_parameters(text, params)

    def _evaluate_condition(self, condition: str, params: Dict[str, Any]) -> bool:
        # 替换 test 表达式中的 #{param} 为 params[param]
        def replacer(match):
            key = match.group(1)
            value = params.get(key)
            if value is None:
                return "None"
            elif isinstance(value, str):
                return f"'{value}'"
            else:
                return str(value)

        expr = re.sub(r"#\{(\w+)\}", replacer, condition)

        # 兼容 test="id != null" 这种写法
        # 先替换 null 为 None
        expr = expr.replace(" null", " None").replace("null", "None")

        # 创建一个安全的评估环境，包含参数值
        eval_env = {}
        for key, value in params.items():
            eval_env[key] = value

        # 对于不在参数中的变量，设置为 None
        # 查找表达式中的所有标识符
        identifiers = re.findall(r"\b[a-zA-Z_]\w*\b", expr)
        for identifier in identifiers:
            if identifier not in eval_env and identifier not in [
                "None",
                "True",
                "False",
            ]:
                eval_env[identifier] = None

        try:
            return bool(eval(expr, {"__builtins__": {}}, eval_env))
        except Exception:
            return False

    def get_sql(self, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Get the SQL statement with parameter substitution.

        Args:
            params: Parameter dictionary

        Returns:
            str: Generated SQL statement
        """
        # Process the root element with parameters
        params = params or {}
        sql = self._process_element(self.root, params)

        # Clean up the SQL
        sql = re.sub(r"\s+", " ", sql).strip()
        # Remove spaces inside parentheses
        sql = re.sub(r"\(\s+", "(", sql)
        sql = re.sub(r"\s+\)", ")", sql)

        return sql
