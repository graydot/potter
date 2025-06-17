// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Potter",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        // Add dependencies here if needed
    ],
    targets: [
        .executableTarget(
            name: "Potter",
            dependencies: [],
            path: "Sources"
        ),
    ]
)
