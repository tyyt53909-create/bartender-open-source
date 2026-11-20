import AppKit
import Foundation

// Read-only; never performs an AX action. Permission belongs to this process.
let app = NSApplication.shared
app.setActivationPolicy(.prohibited)
do {
    let data = try JSONSerialization.data(withJSONObject: Diagnostics.snapshot(),
                                         options: [.prettyPrinted, .sortedKeys])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([10]))
} catch {
    FileHandle.standardError.write(Data("Snapshot serialization failed.\n".utf8))
    exit(1)
}

