import pytest

from autoextract.aio.client import RequestProcessor
from autoextract.aio.errors import QueryError


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


def test_request_processor_with_retries():
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
        handle_retries=True
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

    # An exception should be raised while processing this response
    with pytest.raises(QueryError):
        request_processor.process_results(first_response)

    # Latest results should be equal to our response
    assert request_processor.get_latest_results() == first_response
    # Our pending queries list should contain our query with error
    error_query = first_response[1]
    assert "error" in error_query
    user_query = error_query["query"]["userQuery"]
    assert request_processor.pending_queries == [user_query]

    # Given another error response for this missing query
    second_response = [
        {
            "query": {
                "id": "3",
                "domain": "example.org",
                "userQuery": {
                    "url": "https://example.org/second",
                    "pageType": "article"
                }
            },
            "error": "Proxy error: internal_error",
        },
    ]

    # If we try to process this response,
    # it should raise an exception again
    with pytest.raises(QueryError):
        request_processor.process_results(second_response)

    # Latest results should be equal to a combination of our two responses:
    # successes from previous responses and most up to date errors.
    assert request_processor.get_latest_results() == [
        first_response[0],
        second_response[0],
    ]
    # Our pending queries list should contain our query with error
    error_query = second_response[0]
    assert "error" in error_query
    user_query = error_query["query"]["userQuery"]
    assert request_processor.pending_queries == [user_query]

    # Given another response, this time with a success
    third_response = [
        {
            "query": {
                "id": "4",
                "domain": "example.org",
                "userQuery": {
                    "url": "https://example.org/second",
                    "pageType": "article"
                }
            },
            "article": {
                "name": "My second article",
            },
        },
    ]

    # If we try to process this response
    results = request_processor.process_results(third_response)
    # Results should be equal to a combination of success results
    # from previous and current requests
    assert results == [
        first_response[0],
        third_response[0],
    ]
    # Latest results should be equal to our response
    assert request_processor.get_latest_results() == results
    # Our pending queries list should be empty
    # because there's no additional query to be retried
    assert request_processor.pending_queries == []
