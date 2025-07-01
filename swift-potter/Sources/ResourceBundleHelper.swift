import Foundation

extension Bundle {
    /// Access to the Potter resource bundle without fallbacks
    static var potterResources: Bundle {
        // Look for the bundle in the proper Resources directory
        let bundlePath = Bundle.main.bundleURL
            .appendingPathComponent("Contents/Resources/Potter_Potter.bundle")
        
        guard let bundle = Bundle(url: bundlePath) else {
            // In test environment, use Bundle.module
            return Bundle.module
        }
        
        return bundle
    }
}