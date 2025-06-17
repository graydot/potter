// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Potter",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "Potter",
            targets: ["Potter"]
        ),
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
        .testTarget(
            name: "PotterTests",
            dependencies: ["Potter"],
            path: "Tests"
        ),
    ]
)
