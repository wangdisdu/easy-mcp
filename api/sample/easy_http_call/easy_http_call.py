def easy_http_call(
    method: str, url: str, headers: list, parameters: dict, config: dict
) -> dict:
    """
    Make HTTP request with parameters.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Request URL
        headers: Request headers
        parameters: Request parameters
        config: Tool configuration

    Returns:
        dict: Response data
    """
    import requests

    # Process URL parameters
    if parameters:
        for key, value in list(parameters.items()):
            var = f"{{{key}}}"
            if var in url:
                url = url.replace(var, str(value))
                del parameters[key]

    # Process header parameters
    http_headers = {}
    if headers:
        for header in headers:
            header_key = header["key"]
            header_value = header["value"]
            if parameters:
                for key, value in list(parameters.items()):
                    var = f"{{{key}}}"
                    if var in header_value:
                        header_value = header_value.replace(var, str(value))
                        del parameters[key]
            http_headers[header_key] = header_value

    print(f"url: {url}")
    print(f"method: {method}")
    print(f"headers: {http_headers}")
    print(f"body: {parameters}")

    # Prepare request kwargs
    request_kwargs = {
        "method": method,
        "url": url,
        "headers": http_headers,
        "timeout": 30,
    }

    # Only add json parameter if there are remaining parameters
    if parameters:
        request_kwargs["json"] = parameters

    # Make request
    response = requests.request(**request_kwargs)

    # Return response
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return response.text
