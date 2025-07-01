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
        .package(url: "https://github.com/sparkle-project/Sparkle", from: "2.6.0")
    ],
    targets: [
        .executableTarget(
            name: "Potter",
            dependencies: [
                .product(name: "Sparkle", package: "Sparkle")
            ],
            path: "Sources",
            resources: [
                .copy("Resources")
            ]
        ),
        .testTarget(
            name: "PotterTests",
            dependencies: ["Potter"],
            path: "Tests",
            resources: [
                .copy("../Sources/Resources")
            ]
        ),
    ]
)
