import Foundation

// Simple test for process detection
let task = Process()
task.executableURL = URL(fileURLWithPath: "/bin/ps")
task.arguments = ["-axo", "pid,command"]

let pipe = Pipe()
task.standardOutput = pipe

do {
    try task.run()
    task.waitUntilExit()
    
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    let output = String(data: data, encoding: .utf8) ?? ""
    
    print("=== All processes containing 'Potter' ===")
    for line in output.components(separatedBy: .newlines) {
        if line.contains("Potter") && !line.contains("grep") {
            print(line)
        }
    }
    
    print("\n=== Current PID ===")
    print("Current process PID: \(getpid())")
    
} catch {
    print("Error: \(error)")
}