#!/usr/bin/env swift

import Foundation
import Network

// Simple test to check if our auto-update system can detect versions
func testUpdateDetection() {
    print("🧪 Testing Auto-Update Detection")
    print("================================")
    
    // Test 1: Check if we can fetch the test appcast
    print("📡 Test 1: Fetching test appcast from localhost:8000...")
    
    let url = URL(string: "http://localhost:8000/appcast.xml")!
    let semaphore = DispatchSemaphore(value: 0)
    
    let task = URLSession.shared.dataTask(with: url) { data, response, error in
        defer { semaphore.signal() }
        
        if let error = error {
            print("❌ Failed to fetch appcast: \(error.localizedDescription)")
            return
        }
        
        guard let data = data else {
            print("❌ No data received")
            return
        }
        
        let content = String(data: data, encoding: .utf8) ?? ""
        print("✅ Appcast fetched successfully (\(data.count) bytes)")
        
        // Test 2: Check if we can parse versions
        print("🔍 Test 2: Parsing versions from appcast...")
        
        let versions = parseVersions(from: content)
        print("📋 Found versions: \(versions)")
        
        // Test 3: Version comparison
        print("🔢 Test 3: Testing version comparison...")
        let currentVersion = "2.0.0"
        
        for version in versions {
            let comparison = compareVersions(currentVersion, version)
            let result = comparison == .orderedAscending ? "newer" : 
                        comparison == .orderedDescending ? "older" : "same"
            print("   \(currentVersion) vs \(version): \(result)")
        }
    }
    
    task.resume()
    semaphore.wait()
}

func parseVersions(from appcast: String) -> [String] {
    let pattern = #"sparkle:shortVersionString="([^"]+)""#
    let regex = try! NSRegularExpression(pattern: pattern)
    let matches = regex.matches(in: appcast, range: NSRange(appcast.startIndex..., in: appcast))
    
    return matches.compactMap { match in
        guard let range = Range(match.range(at: 1), in: appcast) else { return nil }
        return String(appcast[range])
    }
}

func compareVersions(_ version1: String, _ version2: String) -> ComparisonResult {
    return version1.compare(version2, options: .numeric)
}

// Test if server is running
func checkServerStatus() {
    print("🌐 Checking if test server is running...")
    
    let url = URL(string: "http://localhost:8000")!
    let semaphore = DispatchSemaphore(value: 0)
    
    let task = URLSession.shared.dataTask(with: url) { data, response, error in
        defer { semaphore.signal() }
        
        if error != nil {
            print("❌ Test server not running. Start it with:")
            print("   cd test_releases && python3 -m http.server 8000")
            return
        }
        
        print("✅ Test server is running")
    }
    
    task.resume()
    _ = semaphore.wait(timeout: .now() + 2)
}

// Run tests
checkServerStatus()
testUpdateDetection()

print("\n🎯 Next Steps:")
print("1. Ensure Potter (version 2.0) is installed in /Applications/")
print("2. Launch Potter and go to Settings → Updates")
print("3. Check current version display")
print("4. Click 'Check for Updates Now'")
print("5. Should find version 2.1.0 available (if server running)")