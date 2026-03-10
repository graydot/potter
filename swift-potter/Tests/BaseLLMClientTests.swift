import XCTest
import Foundation
@testable import Potter

class BaseLLMClientTests: TestBase {

    // MARK: - makeJSONRequest Tests

    func testMakeJSONRequestSetsContentType() throws {
        let url = URL(string: "https://api.example.com/test")!
        let body = ["key": "value"]
        let headers: [String: String] = [:]

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: body)

        XCTAssertEqual(request.value(forHTTPHeaderField: "Content-Type"), "application/json")
    }

    func testMakeJSONRequestSetsHTTPMethod() throws {
        let url = URL(string: "https://api.example.com/test")!
        let body = ["key": "value"]
        let headers: [String: String] = [:]

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: body)

        XCTAssertEqual(request.httpMethod, "POST")
    }

    func testMakeJSONRequestEncodesBody() throws {
        let url = URL(string: "https://api.example.com/test")!
        let body = ["model": "gpt-4", "prompt": "hello"]
        let headers: [String: String] = [:]

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: body)

        XCTAssertNotNil(request.httpBody)
        let decoded = try JSONSerialization.jsonObject(with: request.httpBody!, options: []) as? [String: String]
        XCTAssertEqual(decoded?["model"], "gpt-4")
        XCTAssertEqual(decoded?["prompt"], "hello")
    }

    func testMakeJSONRequestSetsCustomHeaders() throws {
        let url = URL(string: "https://api.example.com/test")!
        let body = ["key": "value"]
        let headers = [
            "Authorization": "Bearer test-key",
            "x-api-key": "my-secret",
            "anthropic-version": "2023-06-01"
        ]

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: body)

        XCTAssertEqual(request.value(forHTTPHeaderField: "Authorization"), "Bearer test-key")
        XCTAssertEqual(request.value(forHTTPHeaderField: "x-api-key"), "my-secret")
        XCTAssertEqual(request.value(forHTTPHeaderField: "anthropic-version"), "2023-06-01")
    }

    // MARK: - Error Handling Tests

    func testHandleLLMErrorFor401() {
        let url = URL(string: "https://api.example.com/test")!
        let httpResponse = HTTPURLResponse(
            url: url,
            statusCode: 401,
            httpVersion: nil,
            headerFields: nil
        )!
        let data = "Unauthorized".data(using: .utf8)!

        let error = LLMHTTPClient.handleLLMError(httpResponse: httpResponse, data: data, provider: "TestProvider")

        if case .network(.unauthorized(let provider)) = error {
            XCTAssertEqual(provider, "TestProvider")
        } else {
            XCTFail("Expected .network(.unauthorized), got \(error)")
        }
    }

    func testHandleLLMErrorFor429() {
        let url = URL(string: "https://api.example.com/test")!
        let httpResponse = HTTPURLResponse(
            url: url,
            statusCode: 429,
            httpVersion: nil,
            headerFields: nil
        )!
        let data = "Rate limit exceeded".data(using: .utf8)!

        let error = LLMHTTPClient.handleLLMError(httpResponse: httpResponse, data: data, provider: "TestProvider")

        if case .network(.serverError(let statusCode, let message)) = error {
            XCTAssertEqual(statusCode, 429)
            XCTAssertEqual(message, "Rate limit exceeded")
        } else {
            XCTFail("Expected .network(.serverError) with status 429, got \(error)")
        }
    }

    func testHandleLLMErrorFor500() {
        let url = URL(string: "https://api.example.com/test")!
        let httpResponse = HTTPURLResponse(
            url: url,
            statusCode: 500,
            httpVersion: nil,
            headerFields: nil
        )!
        let data = "Internal Server Error".data(using: .utf8)!

        let error = LLMHTTPClient.handleLLMError(httpResponse: httpResponse, data: data, provider: "TestProvider")

        if case .network(.serverError(let statusCode, let message)) = error {
            XCTAssertEqual(statusCode, 500)
            XCTAssertEqual(message, "Internal Server Error")
        } else {
            XCTFail("Expected .network(.serverError) with status 500, got \(error)")
        }
    }

    // MARK: - Retry After Extraction Tests

    func testExtractRetryAfterFromMessage() {
        let message = "Rate limit exceeded. Please retry after 30 seconds."
        let result = LLMHTTPClient.extractRetryAfterFromMessage(message)
        XCTAssertEqual(result, 30.0)
    }

    func testExtractRetryAfterReturnsNilForNoMatch() {
        let message = "Something went wrong with the API"
        let result = LLMHTTPClient.extractRetryAfterFromMessage(message)
        XCTAssertNil(result)
    }
}
