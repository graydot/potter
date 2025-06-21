#!/usr/bin/env swift

import Foundation

print("🔧 Potter Storage Fix Tool")
print("This will reset storage to UserDefaults mode to fix the keychain access issue.\n")

// Reset storage method to UserDefaults for all providers
UserDefaults.standard.set("userdefaults", forKey: "storage_method")

let providers = ["openai", "anthropic", "google"]
for provider in providers {
    let methodKey = "api_key_storage_method_\(provider)"
    UserDefaults.standard.set("userdefaults", forKey: methodKey)
    print("✅ Reset \(provider) storage method to UserDefaults")
}

// Force synchronization
UserDefaults.standard.synchronize()

print("\n✅ Storage reset complete!")
print("📝 All API key storage is now set to UserDefaults mode.")
print("🔄 Please restart Potter and re-enter your API keys in the settings.")