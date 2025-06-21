#!/usr/bin/env swift

import Foundation

// Simple script to debug storage issues

print("=== Potter Storage Debug ===")

// Check UserDefaults
let defaults = UserDefaults.standard
print("\n1. Checking UserDefaults:")

let providers = ["openai", "anthropic", "google"]
for provider in providers {
    let keyPath = "api_key_\(provider)"
    let methodPath = "api_key_storage_method_\(provider)"
    
    let key = defaults.string(forKey: keyPath)
    let method = defaults.string(forKey: methodPath)
    
    print("  \(provider):")
    print("    key: \(key != nil ? "EXISTS" : "MISSING")")
    print("    method: \(method ?? "default")")
}

// Check overall storage method
let storageMethod = defaults.string(forKey: "storage_method")
print("\n2. Overall storage method: \(storageMethod ?? "default")")

// Check if there are any other Potter-related keys
print("\n3. All Potter-related UserDefaults keys:")
for (key, value) in defaults.dictionaryRepresentation() {
    if key.lowercased().contains("api") || key.lowercased().contains("potter") || key.lowercased().contains("storage") {
        print("  \(key): \(value)")
    }
}