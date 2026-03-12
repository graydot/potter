import XCTest
@testable import Potter

// MARK: - Streaming Response Type Tests
//
// We can't easily run full end-to-end streaming tests without a live API key,
// but we can verify the decodable streaming chunk types and test that the
// MockLLMProcessor's streamText drives onToken correctly.

final class StreamingChunkDecodingTests: XCTestCase {

    // MARK: OpenAI streaming chunk

    func testOpenAIStreamChunkDecodesContent() throws {
        let json = """
        {"choices":[{"delta":{"content":"Hello"}}]}
        """.data(using: .utf8)!
        let chunk = try JSONDecoder().decode(OpenAIStreamChunk.self, from: json)
        XCTAssertEqual(chunk.choices.first?.delta.content, "Hello")
    }

    func testOpenAIStreamChunkDecodesNilContent() throws {
        let json = """
        {"choices":[{"delta":{}}]}
        """.data(using: .utf8)!
        let chunk = try JSONDecoder().decode(OpenAIStreamChunk.self, from: json)
        XCTAssertNil(chunk.choices.first?.delta.content)
    }

    func testOpenAIStreamChunkDecodesEmptyChoices() throws {
        let json = """
        {"choices":[]}
        """.data(using: .utf8)!
        let chunk = try JSONDecoder().decode(OpenAIStreamChunk.self, from: json)
        XCTAssertTrue(chunk.choices.isEmpty)
    }

    // MARK: Anthropic streaming delta

    func testAnthropicStreamDeltaDecodesContentBlockDelta() throws {
        let json = """
        {"type":"content_block_delta","delta":{"type":"text_delta","text":"world"}}
        """.data(using: .utf8)!
        let delta = try JSONDecoder().decode(AnthropicStreamDelta.self, from: json)
        XCTAssertEqual(delta.type, "content_block_delta")
        XCTAssertEqual(delta.delta?.text, "world")
    }

    func testAnthropicStreamDeltaDecodesNonContentEvent() throws {
        let json = """
        {"type":"message_start"}
        """.data(using: .utf8)!
        let delta = try JSONDecoder().decode(AnthropicStreamDelta.self, from: json)
        XCTAssertEqual(delta.type, "message_start")
        XCTAssertNil(delta.delta)
    }
}

// MARK: - MockLLMProcessor streamText tests

final class MockLLMStreamingTests: XCTestCase {

    private var mock: MockLLMProcessor!

    override func setUp() {
        super.setUp()
        mock = MockLLMProcessor()
        mock.responseText = "one two three"
    }

    func testStreamTextCallsOnTokenForEachWord() async throws {
        // Use a class (reference type, not a captured var) to avoid Swift 6 concurrency warning.
        final class Collector: @unchecked Sendable {
            var tokens: [String] = []
            func add(_ t: String) { tokens.append(t) }
        }
        let collector = Collector()
        _ = try await mock.streamText("input", prompt: "p") { token in
            collector.add(token)
        }
        // MockLLMProcessor splits on spaces and emits each word + space
        XCTAssertFalse(collector.tokens.isEmpty)
        let assembled = collector.tokens.joined()
        XCTAssertTrue(assembled.contains("one"))
        XCTAssertTrue(assembled.contains("two"))
        XCTAssertTrue(assembled.contains("three"))
    }

    func testStreamTextReturnsFullResponse() async throws {
        let result = try await mock.streamText("input", prompt: "p") { _ in }
        XCTAssertEqual(result, "one two three")
    }

    func testStreamTextThrowsOnFailure() async {
        mock.shouldFail = true
        do {
            _ = try await mock.streamText("input", prompt: "p") { _ in }
            XCTFail("Expected error to be thrown")
        } catch {
            XCTAssertNotNil(error)
        }
    }

    func testStreamTextDoesNotCallOnTokenOnFailure() async {
        final class Counter: @unchecked Sendable { var count = 0 }
        mock.shouldFail = true
        let counter = Counter()
        _ = try? await mock.streamText("input", prompt: "p") { _ in counter.count += 1 }
        XCTAssertEqual(counter.count, 0)
    }
}

// MARK: - LLMProcessing protocol streaming

final class LLMProcessingStreamingConformanceTests: XCTestCase {

    @MainActor
    func testLLMManagerConformsToStreamTextProtocol() {
        // Just confirm the protocol conformance compiles
        let manager: any LLMProcessing = LLMManager()
        XCTAssertNotNil(manager)
    }
}
