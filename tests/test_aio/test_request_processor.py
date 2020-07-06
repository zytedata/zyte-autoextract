from autoextract.aio.client import RequestProcessor


def test_request_processor_without_retries():
    # Given an initial query with two items
    initial_query = [
        {
            "url": "https://example.org/first",
            "pageType": "article",
        },
        {
            "url": "https://example.org/second",
            "pageType": "article",
        },
    ]

    # Initialize our request processor with this query
    request_processor = RequestProcessor(
        query=initial_query,
        handle_retries=False
    )

    # Since we haven't processed any response yet,
    # our request processor should have:
    #
    # Empty results
    assert request_processor.get_latest_results() == []
    # Pending queries list equal to our initial query
    assert request_processor.pending_queries == initial_query

    # Given our first response with a success and an error
    first_response = [
        {
            "query": {
                "id": "1",
                "domain": "example.org",
                "userQuery": {
                    "url": "https://example.org/first",
                    "pageType": "article"
                }
            },
            "article": {
                "name": "My first article",
            },
        },
        {
            "query": {
                "id": "2",
                "domain": "example.org",
                "userQuery": {
                    "url": "https://example.org/second",
                    "pageType": "article"
                }
            },
            "error": "Proxy error: internal_error",
        },
    ]

    # Process this response
    results = request_processor.process_results(first_response)

    # Results should be equal to our response
    assert results == first_response
    # Latest results should be equal to our response
    assert request_processor.get_latest_results() == results
    # Our pending queries list should be empty
    # because retry is disabled
    assert request_processor.pending_queries == []
