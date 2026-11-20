import AppKit
import ApplicationServices

enum Diagnostics {
    static let fixtureBundle = "org.menuvalidation.Fixture"
    final class AXReadBudget {
        var nodesLeft = 48
        let deadline = ProcessInfo.processInfo.systemUptime + 2.5
        var permitsCall: Bool { ProcessInfo.processInfo.systemUptime < deadline }
        var exhausted: Bool { nodesLeft == 0 || !permitsCall }
        func enterNode() -> Bool {
            guard nodesLeft > 0 && permitsCall else { return false }
            nodesLeft -= 1
            return true
        }
    }
    static func timestamp() -> String {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f.string(from: Date())
    }
    static func rect(_ r: CGRect) -> [String: Double] {
        ["x": Double(r.minX), "y": Double(r.minY),
         "width": Double(r.width), "height": Double(r.height)]
    }
    static func screens() -> [[String: Any]] {
        NSScreen.screens.enumerated().map { index, s in
            var record: [String: Any] = [
                "index": index, "frame_appkit_points": rect(s.frame),
                "visible_frame_appkit_points": rect(s.visibleFrame),
                "backing_scale": Double(s.backingScaleFactor),
                "safe_top_points": Double(s.safeAreaInsets.top),
                "coordinate_space": "AppKit global points, bottom-left origin"
            ]
            if let area = s.auxiliaryTopRightArea {
                record["auxiliary_top_right_appkit_points"] = rect(area)
            }
            return record
        }
    }
    static func attribute(_ item: AXUIElement, _ name: CFString, budget: AXReadBudget) -> CFTypeRef? {
        guard budget.permitsCall else { return nil }
        var result: CFTypeRef?
        return AXUIElementCopyAttributeValue(item, name, &result) == .success ? result : nil
    }
    static func frame(_ item: AXUIElement, budget: AXReadBudget) -> CGRect? {
        guard let pv = attribute(item, kAXPositionAttribute as CFString, budget: budget),
              let sv = attribute(item, kAXSizeAttribute as CFString, budget: budget),
              CFGetTypeID(pv) == AXValueGetTypeID(),
              CFGetTypeID(sv) == AXValueGetTypeID() else { return nil }
        var p = CGPoint.zero
        var s = CGSize.zero
        guard AXValueGetValue(pv as! AXValue, .cgPoint, &p),
              AXValueGetValue(sv as! AXValue, .cgSize, &s) else { return nil }
        return CGRect(origin: p, size: s)
    }
    static func inspect(_ item: AXUIElement, depth: Int, budget: AXReadBudget) -> [String: Any] {
        guard budget.enterNode() else { return ["status": "observation_budget_exhausted"] }
        // Apple documents that timeout applies only to this exact AX object.
        // Set it on every node, not only the producing application's element.
        guard AXUIElementSetMessagingTimeout(item, 0.15) == .success else {
            return ["status": "messaging_timeout_configuration_failed"]
        }
        var record: [String: Any] = [:]
        // Inspect only our synthetic Fixture, never all applications.
        for name in ["AXIdentifier", "AXTitle", "AXDescription", "AXRole", "AXValue"] {
            if let value = attribute(item, name as CFString, budget: budget) {
                if let s = value as? String { record[name] = String(s.prefix(256)) }
                else if let n = value as? NSNumber { record[name] = n }
            }
        }
        if let r = frame(item, budget: budget) {
            record["frame_ax_points"] = rect(r)
            record["coordinate_space"] = "Accessibility global points, top-left origin"
        }
        var actions: CFArray?
        if budget.permitsCall && AXUIElementCopyActionNames(item, &actions) == .success {
            record["declared_actions"] = actions as? [String] ?? []
        }
        if depth < 3, let children = attribute(item, kAXChildrenAttribute as CFString, budget: budget) as? [AXUIElement] {
            var observed: [[String: Any]] = []
            for child in children.prefix(32) {
                guard !budget.exhausted else { break }
                observed.append(inspect(child, depth: depth + 1, budget: budget))
            }
            record["children"] = observed
            record["children_truncated"] = children.count > observed.count
        }
        record["budget_exhausted"] = budget.exhausted
        return record
    }
    static func fixtureInventory() -> [String: Any] {
        guard AXIsProcessTrusted() else {
            return ["status": "permission_missing", "bundle": fixtureBundle,
                    "action": "read_only", "completeness": "unknown"]
        }
        let apps = NSRunningApplication.runningApplications(withBundleIdentifier: fixtureBundle)
        if apps.isEmpty {
            return ["status": "fixture_not_running", "bundle": fixtureBundle,
                    "action": "read_only", "completeness": "unknown"]
        }
        var entries: [[String: Any]] = []
        let budget = AXReadBudget()
        for app in apps.prefix(4) {
            guard !budget.exhausted else { break }
            let element = AXUIElementCreateApplication(app.processIdentifier)
            guard AXUIElementSetMessagingTimeout(element, 0.15) == .success else {
                entries.append(["pid": Int(app.processIdentifier), "status": "messaging_timeout_configuration_failed"])
                continue
            }
            var raw: CFTypeRef?
            let error = AXUIElementCopyAttributeValue(element, "AXExtrasMenuBar" as CFString, &raw)
            var result: [String: Any] = ["pid": Int(app.processIdentifier), "ax_error": error.rawValue]
            if error == .success, let raw = raw, CFGetTypeID(raw) == AXUIElementGetTypeID() {
                result["extras_menu_bar"] = inspect(raw as! AXUIElement, depth: 0, budget: budget)
            } else {
                result["status"] = "inventory_unavailable_via_producer"
            }
            entries.append(result)
        }
        return ["status": "observed", "bundle": fixtureBundle, "processes": entries,
                "action": "read_only", "completeness": "unknown",
                "budget_exhausted": budget.exhausted, "node_budget": 48,
                "time_budget_seconds": 2.5, "messaging_timeout_seconds": 0.15,
                "budget_is_hard_runtime_guarantee": false,
                "note": "An empty AX result does not prove item absence. Host-process lookup is not implemented."]
    }
    static func snapshot() -> [String: Any] {
        let v = ProcessInfo.processInfo.operatingSystemVersion
        return [
            "schema": "menuvalidation.snapshot.v1", "timestamp": timestamp(),
            "evidence_level": "machine_observation_not_task_verdict",
            "os": ["major": v.majorVersion, "minor": v.minorVersion, "patch": v.patchVersion,
                   "description": ProcessInfo.processInfo.operatingSystemVersionString],
            "screens": screens(),
            "permissions": ["accessibility_trusted_for_this_process": AXIsProcessTrusted(),
                            "screen_capture_requested": false],
            "fixture": fixtureInventory()
        ]
    }
}

