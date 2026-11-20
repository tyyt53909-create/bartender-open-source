// SPDX-License-Identifier: MIT
// Original validation fixture. No third-party application state is read or changed.
import AppKit
import Foundation

final class FixtureLogger {
    let runID = UUID().uuidString
    let fileURL: URL
    private let handle: FileHandle
    private let formatter = ISO8601DateFormatter()
    private var bytesWritten = 0
    private var sequence = 0
    private let limit = 8 * 1024 * 1024
    private(set) var loggingProblem: String?

    init() throws {
        let support = try FileManager.default.url(for: .applicationSupportDirectory,
                                                   in: .userDomainMask,
                                                   appropriateFor: nil,
                                                   create: true)
        let directory = support.appendingPathComponent("MenuBarValidationLab/Fixture", isDirectory: true)
        try FileManager.default.createDirectory(at: directory,
                                                withIntermediateDirectories: true,
                                                attributes: [.posixPermissions: 0o700])
        fileURL = directory.appendingPathComponent("fixture-\(runID).jsonl")
        guard FileManager.default.createFile(atPath: fileURL.path, contents: nil,
                                             attributes: [.posixPermissions: 0o600]) else {
            throw NSError(domain: "MenuBarFixture", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "Could not create the fixture log."])
        }
        handle = try FileHandle(forWritingTo: fileURL)
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    }

    deinit { try? handle.close() }

    func write(_ event: String, itemID: String? = nil, sessionID: String? = nil,
               details: [String: Any] = [:]) {
        guard loggingProblem == nil else { return }
        if bytesWritten >= limit {
            loggingProblem = "Log reached 8 MiB. Start a new run before continuing."
            // Explicitly record that subsequent observations are unavailable.
            append("loggingStopped", details: ["reason": "size_limit", "limitBytes": limit])
            return
        }
        append(event, itemID: itemID, sessionID: sessionID, details: details)
    }

    private func append(_ event: String, itemID: String? = nil, sessionID: String? = nil,
                        details: [String: Any] = [:]) {
        sequence += 1
        var row: [String: Any] = [
            "schemaVersion": 1,
            "sequence": sequence,
            "event": event,
            "timestamp": formatter.string(from: Date()),
            "monotonicSeconds": ProcessInfo.processInfo.systemUptime,
            "fixtureRunID": runID,
            "bundleID": "org.menuvalidation.Fixture",
            "details": details
        ]
        if let itemID = itemID { row["itemID"] = itemID }
        if let sessionID = sessionID { row["sessionID"] = sessionID }
        do {
            var data = try JSONSerialization.data(withJSONObject: row, options: [.sortedKeys])
            data.append(0x0A)
            try handle.write(contentsOf: data)
            bytesWritten += data.count
        } catch {
            loggingProblem = "Log write failed: \(error.localizedDescription)"
            fputs("Menu Bar Fixture: observation log failed; this run is incomplete.\n", stderr)
        }
    }

    func snapshot() throws -> Data {
        try handle.synchronize()
        return try Data(contentsOf: fileURL)
    }
}

struct FixtureItem {
    let id: String
    let axID: String
    let label: String
    let statusItem: NSStatusItem
}

struct MenuIdentity {
    let itemID: String
    let sessionID: String
    let variant: String
    let depth: Int
}

final class FixtureDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private var logger: FixtureLogger?
    private var items: [FixtureItem] = []
    private var menuIdentities: [ObjectIdentifier: MenuIdentity] = [:]
    private var menuStarts: [ObjectIdentifier: TimeInterval] = [:]
    private var activeMenuSessions = Set<String>()
    private var counter = 0
    private var ticks = 0
    private var counterPaused = false
    private var timer: Timer?
    private var localScrollMonitor: Any?
    private var lastLayoutData: Data?
    private var controlWindow: NSWindow?
    private var statusField: NSTextField?
    private var logField: NSTextField?
    private var pauseButton: NSButton?
    private var lastAction = "No action observed yet."

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            logger = try FixtureLogger()
        } catch {
            showError("Cannot start an observable run", error.localizedDescription)
            NSApp.terminate(nil)
            return
        }

        createStatusItems()
        logger?.write("fixtureStarted", details: [
            "operatingSystem": ProcessInfo.processInfo.operatingSystemVersionString,
            "pid": ProcessInfo.processInfo.processIdentifier,
            "counterPeriodSeconds": 1,
            "itemIDs": items.map { $0.id },
            "axIDs": items.map { $0.axID },
            "buildScope": "source-built validation fixture; no compatibility claim"
        ])
        updateCounterAppearance()
        recordLayout(reason: "launch", force: true)

        timer = Timer(timeInterval: 1, target: self, selector: #selector(tick),
                      userInfo: nil, repeats: true)
        if let timer = timer {
            RunLoop.main.add(timer, forMode: .common)
            // Explicit registration makes the intended tracking behavior clear.
            // stateChanged logs, not this registration, prove behavior on a tested Mac.
            RunLoop.main.add(timer, forMode: .eventTracking)
        }
        localScrollMonitor = NSEvent.addLocalMonitorForEvents(matching: .scrollWheel) { [weak self] event in
            self?.observeOwnScroll(event)
            return event
        }
        NotificationCenter.default.addObserver(self, selector: #selector(screensChanged(_:)),
                                                name: NSApplication.didChangeScreenParametersNotification,
                                                object: nil)
        NSWorkspace.shared.notificationCenter.addObserver(self, selector: #selector(didWake(_:)),
                                                           name: NSWorkspace.didWakeNotification,
                                                           object: nil)
        showControlWindow(reason: "manual_app_launch")
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        showControlWindow(reason: "manual_reopen")
        return false
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        logger?.write("fixtureActivated")
    }

    func applicationDidResignActive(_ notification: Notification) {
        logger?.write("fixtureDeactivated")
    }

    func applicationWillTerminate(_ notification: Notification) {
        timer?.invalidate()
        if let monitor = localScrollMonitor { NSEvent.removeMonitor(monitor) }
        NotificationCenter.default.removeObserver(self)
        NSWorkspace.shared.notificationCenter.removeObserver(self)
        logger?.write("fixtureStopping", details: ["activeMenuSessions": Array(activeMenuSessions).sorted()])
        for item in items { NSStatusBar.system.removeStatusItem(item.statusItem) }
        try? logger?.snapshot()
    }

    private func createStatusItems() {
        for (id, label, title, length) in [
            ("alpha", "Fixture Alpha", "FA", CGFloat(34)),
            ("beta", "Fixture Beta", "B 000", CGFloat(62)),
            ("gamma", "Fixture Gamma", "FC", CGFloat(34))
        ] {
            let statusItem = NSStatusBar.system.statusItem(withLength: length)
            statusItem.autosaveName = "org.menuvalidation.fixture.\(id)"
            guard let button = statusItem.button else { continue }
            button.title = title
            button.toolTip = "\(label): left / right / Option click; submenu; local scroll observation"
            button.font = NSFont.monospacedDigitSystemFont(ofSize: 12, weight: .regular)
            button.target = self
            button.action = #selector(statusItemActivated(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
            let axID = "org.menuvalidation.fixture.\(id)"
            button.setAccessibilityIdentifier(axID)
            button.setAccessibilityLabel(label)
            button.setAccessibilityHelp("Validation fixture \(id). Opens its own native menu.")
            items.append(FixtureItem(id: id, axID: axID, label: label, statusItem: statusItem))
        }
    }

    @objc private func tick() {
        ticks += 1
        if !counterPaused {
            counter = (counter + 1) % 1000
            updateCounterAppearance()
            logger?.write("stateChanged", itemID: "beta", details: [
                "counter": counter,
                "visibleTitle": String(format: "B %03d", counter),
                "activeMenuSessions": Array(activeMenuSessions).sorted()
            ])
        }
        recordLayout(reason: "timer", force: ticks % 10 == 0)
        updateControlLabels()
    }

    private func updateCounterAppearance() {
        guard let button = items.first(where: { $0.id == "beta" })?.statusItem.button else { return }
        button.title = String(format: "B %03d", counter)
        button.setAccessibilityValue(String(counter))
        NSAccessibility.post(element: button, notification: .valueChanged)
    }

    private func activationDetails(for button: NSStatusBarButton) -> [String: Any] {
        guard let event = NSApp.currentEvent else {
            return ["variant": "unknown", "eventAttribution": "no_current_app_event"]
        }
        let age = ProcessInfo.processInfo.systemUptime - event.timestamp
        let buttonEvent = event.type == .leftMouseUp || event.type == .rightMouseUp
        let sameWindow = button.window.map { event.windowNumber == $0.windowNumber } ?? false
        guard buttonEvent, sameWindow, age >= 0, age < 0.5 else {
            // AXPress/keyboard input may have no contemporaneous pointer event.
            // Do not infer their source from an old NSEvent or assert "AX succeeded".
            return ["variant": "unknown", "eventAttribution": "no_recent_matching_pointer_event"]
        }
        let right = event.type == .rightMouseUp
        let option = event.modifierFlags.contains(.option)
        let variant = right ? (option ? "right+option" : "right") : (option ? "option" : "left")
        return [
            "variant": variant,
            "eventAttribution": "recent_own_pointer_event",
            "eventTypeRaw": event.type.rawValue,
            "modifierFlagsRaw": event.modifierFlags.rawValue,
            "eventAgeSeconds": age
        ]
    }

    @objc private func statusItemActivated(_ sender: NSStatusBarButton) {
        guard let item = items.first(where: { $0.statusItem.button === sender }) else { return }
        let sessionID = UUID().uuidString
        let details = activationDetails(for: sender)
        let variant = details["variant"] as? String ?? "unknown"
        logger?.write("activation", itemID: item.id, sessionID: sessionID, details: details)
        lastAction = "\(item.label): \(variant)"
        let menu = makeMenu(item: item, variant: variant, sessionID: sessionID)
        let selected = menu.popUp(positioning: nil, at: NSPoint(x: sender.bounds.minX, y: sender.bounds.minY),
                                  in: sender)
        logger?.write("menuTrackingReturned", itemID: item.id, sessionID: sessionID,
                      details: ["itemSelected": selected])
        let keys = menuIdentities.filter { $0.value.sessionID == sessionID }.map { $0.key }
        for key in keys {
            menuIdentities.removeValue(forKey: key)
            menuStarts.removeValue(forKey: key)
        }
        activeMenuSessions.remove(sessionID)
        updateControlLabels()
    }

    private func makeMenu(item: FixtureItem, variant: String, sessionID: String) -> NSMenu {
        let menu = NSMenu(title: item.label)
        menu.autoenablesItems = false
        menu.delegate = self
        menuIdentities[ObjectIdentifier(menu)] = MenuIdentity(itemID: item.id, sessionID: sessionID,
                                                            variant: variant, depth: 0)
        let title = NSMenuItem(title: "\(item.label) · \(variant)", action: nil, keyEquivalent: "")
        title.isEnabled = false
        menu.addItem(title)
        let hold = NSMenuItem(title: "Leave open ≥ 5 s; the fixture never auto-closes it",
                              action: nil, keyEquivalent: "")
        hold.isEnabled = false
        menu.addItem(hold)
        menu.addItem(.separator())
        menu.addItem(command(title: "Select \(item.label) action", commandID: "primary",
                             item: item, variant: variant, sessionID: sessionID))

        let submenu = NSMenu(title: "\(item.label) submenu")
        submenu.autoenablesItems = false
        submenu.delegate = self
        menuIdentities[ObjectIdentifier(submenu)] = MenuIdentity(itemID: item.id, sessionID: sessionID,
                                                               variant: variant, depth: 1)
        submenu.addItem(command(title: "Select \(item.label) submenu action", commandID: "submenu",
                                item: item, variant: variant, sessionID: sessionID))
        let submenuItem = NSMenuItem(title: "\(item.label) submenu", action: nil, keyEquivalent: "")
        submenuItem.submenu = submenu
        menu.addItem(submenuItem)
        menu.addItem(.separator())
        let controls = NSMenuItem(title: "Open fixture controls…",
                                  action: #selector(openControls(_:)), keyEquivalent: "")
        controls.target = self
        menu.addItem(controls)
        let quit = NSMenuItem(title: "Quit fixture", action: #selector(quitFixture(_:)), keyEquivalent: "")
        quit.target = self
        menu.addItem(quit)
        return menu
    }

    private func command(title: String, commandID: String, item: FixtureItem,
                         variant: String, sessionID: String) -> NSMenuItem {
        let entry = NSMenuItem(title: title, action: #selector(actionSelected(_:)), keyEquivalent: "")
        entry.target = self
        entry.representedObject = [
            "itemID": item.id, "sessionID": sessionID, "commandID": commandID, "variant": variant
        ]
        return entry
    }

    @objc private func actionSelected(_ sender: NSMenuItem) {
        guard let info = sender.representedObject as? [String: String] else { return }
        logger?.write("actionSelected", itemID: info["itemID"], sessionID: info["sessionID"],
                      details: ["commandID": info["commandID"] ?? "", "variant": info["variant"] ?? ""])
        lastAction = "\(info["itemID"] ?? "?") / \(info["variant"] ?? "?") / \(info["commandID"] ?? "?")"
    }

    func menuWillOpen(_ menu: NSMenu) {
        let key = ObjectIdentifier(menu)
        guard let meta = menuIdentities[key] else { return }
        menuStarts[key] = ProcessInfo.processInfo.systemUptime
        activeMenuSessions.insert(meta.sessionID)
        logger?.write(meta.depth == 0 ? "menuOpened" : "submenuOpened",
                      itemID: meta.itemID, sessionID: meta.sessionID,
                      details: ["variant": meta.variant, "depth": meta.depth, "counter": counter])
    }

    func menuDidClose(_ menu: NSMenu) {
        let key = ObjectIdentifier(menu)
        guard let meta = menuIdentities[key] else { return }
        var details: [String: Any] = ["variant": meta.variant, "depth": meta.depth, "counter": counter]
        if let start = menuStarts.removeValue(forKey: key) {
            details["openDurationSeconds"] = max(0, ProcessInfo.processInfo.systemUptime - start)
        }
        logger?.write(meta.depth == 0 ? "menuClosed" : "submenuClosed",
                      itemID: meta.itemID, sessionID: meta.sessionID, details: details)
        if meta.depth == 0 { activeMenuSessions.remove(meta.sessionID) }
    }

    private func observeOwnScroll(_ event: NSEvent) {
        // A local monitor receives only events delivered to this app. No global monitor.
        // macOS hosting changes may prevent these events reaching this process.
        guard let eventWindow = event.window else { return }
        for item in items {
            guard let button = item.statusItem.button, button.window === eventWindow else { continue }
            let local = button.convert(event.locationInWindow, from: nil)
            guard button.bounds.contains(local) else { continue }
            logger?.write("scrollObserved", itemID: item.id, details: [
                "deltaX": Double(event.scrollingDeltaX), "deltaY": Double(event.scrollingDeltaY),
                "phaseRaw": event.phase.rawValue, "momentumPhaseRaw": event.momentumPhase.rawValue
            ])
            return
        }
    }

    @objc private func screensChanged(_ notification: Notification) {
        recordLayout(reason: "screen_parameters_changed", force: true)
    }
    @objc private func didWake(_ notification: Notification) {
        logger?.write("fixtureWakeObserved")
        recordLayout(reason: "wake", force: true)
    }

    private func recordLayout(reason: String, force: Bool) {
        let rows: [[String: Any]] = items.map { item in
            var row: [String: Any] = ["itemID": item.id, "axID": item.axID,
                                      "statusItemIsVisible": item.statusItem.isVisible]
            if let button = item.statusItem.button, let window = button.window {
                let rect = window.convertToScreen(button.convert(button.bounds, to: nil))
                row["frameAppKit"] = ["x": Double(rect.origin.x), "y": Double(rect.origin.y),
                                      "width": Double(rect.width), "height": Double(rect.height)]
                row["windowNumber"] = window.windowNumber
                row["backingScale"] = Double(window.backingScaleFactor)
            } else {
                row["presentation"] = "no_local_button_window"
            }
            return row
        }
        let screens: [[String: Any]] = NSScreen.screens.enumerated().map { index, screen in
            ["index": index,
             "frameAppKit": ["x": Double(screen.frame.origin.x), "y": Double(screen.frame.origin.y),
                             "width": Double(screen.frame.width), "height": Double(screen.frame.height)],
             "backingScale": Double(screen.backingScaleFactor),
             "safeAreaTop": Double(screen.safeAreaInsets.top)]
        }
        let payload: [String: Any] = ["items": rows, "screens": screens]
        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys]) else { return }
        guard force || data != lastLayoutData else { return }
        lastLayoutData = data
        logger?.write("layoutObserved", details: [
            "reason": reason, "items": rows, "screens": screens,
            "coordinateSpace": "AppKit global points; origin is not CG/AX top-left",
            "visibilityWarning": "isVisible and local frame do not prove actual on-screen visibility"
        ])
    }

    @objc private func openControls(_ sender: Any?) {
        // Let NSMenu finish tracking before intentionally activating our own controls.
        DispatchQueue.main.async { [weak self] in self?.showControlWindow(reason: "manual_menu_action") }
    }

    private func showControlWindow(reason: String) {
        if controlWindow == nil { makeControlWindow() }
        updateControlLabels()
        logger?.write("controlsRequested", details: ["reason": reason])
        controlWindow?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func makeControlWindow() {
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 700, height: 570),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Menu Bar Validation Fixture"
        window.isReleasedWhenClosed = false
        window.contentMinSize = NSSize(width: 660, height: 530)
        window.center()
        let title = NSTextField(labelWithString: "One application · three distinct menu bar items")
        title.font = .boldSystemFont(ofSize: 17)
        let summary = NSTextField(wrappingLabelWithString:
            "FA = Alpha · B 000 = Beta (counter changes each second) · FC = Gamma.\n" +
            "Try left, right and Option click; then leave a menu or submenu open. " +
            "The fixture does not close menus on a timer or control another application.")
        let instructions = NSTextField(wrappingLabelWithString:
            "Run the same tasks with no manager first, then with one candidate manager. " +
            "Hide this control window during interaction tests. A missing event is an observation gap, not a pass.")
        let status = NSTextField(wrappingLabelWithString: "")
        status.font = .monospacedSystemFont(ofSize: 12, weight: .regular)
        statusField = status
        let path = NSTextField(wrappingLabelWithString: "")
        path.isSelectable = true
        path.font = .systemFont(ofSize: 11)
        logField = path
        let pause = NSButton(title: "Pause counter", target: self, action: #selector(toggleCounter(_:)))
        pauseButton = pause
        let row1 = NSStackView(views: [
            pause,
            NSButton(title: "New run / reset", target: self, action: #selector(newRun(_:))),
            NSButton(title: "Snapshot layout", target: self, action: #selector(snapshotLayout(_:)))
        ])
        row1.orientation = .horizontal
        row1.spacing = 10
        let row2 = NSStackView(views: [
            NSButton(title: "Export JSONL…", target: self, action: #selector(exportLog(_:))),
            NSButton(title: "Reveal log", target: self, action: #selector(revealLog(_:))),
            NSButton(title: "Hide controls", target: self, action: #selector(hideControls(_:))),
            NSButton(title: "Quit fixture", target: self, action: #selector(quitFixture(_:)))
        ])
        row2.orientation = .horizontal
        row2.spacing = 10
        let stack = NSStackView(views: [title, summary, instructions, status, path, row1, row2])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        if let content = window.contentView {
            content.addSubview(stack)
            NSLayoutConstraint.activate([
                stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 22),
                stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -22),
                stack.topAnchor.constraint(equalTo: content.topAnchor, constant: 22),
                stack.bottomAnchor.constraint(lessThanOrEqualTo: content.bottomAnchor, constant: -22),
                summary.widthAnchor.constraint(equalTo: stack.widthAnchor),
                instructions.widthAnchor.constraint(equalTo: stack.widthAnchor),
                status.widthAnchor.constraint(equalTo: stack.widthAnchor),
                path.widthAnchor.constraint(equalTo: stack.widthAnchor)
            ])
        }
        controlWindow = window
    }

    private func updateControlLabels() {
        let problem = logger?.loggingProblem.map { "\nINCOMPLETE LOG: \($0)" } ?? ""
        statusField?.stringValue = "Run: \(logger?.runID ?? "unavailable")\n" +
            "Counter: \(counter) · \(counterPaused ? "paused" : "running")\n" +
            "Last activation/action: \(lastAction)" + problem
        logField?.stringValue = "Own-event log: \(logger?.fileURL.path ?? "unavailable")"
        pauseButton?.title = counterPaused ? "Resume counter" : "Pause counter"
    }

    @objc private func toggleCounter(_ sender: Any?) {
        counterPaused.toggle()
        logger?.write("counterPausedChanged", itemID: "beta", details: ["paused": counterPaused, "counter": counter])
        updateControlLabels()
    }

    @objc private func newRun(_ sender: Any?) {
        guard activeMenuSessions.isEmpty else {
            showError("Close the fixture menu first", "Starting a new run during an open menu would split its observations.")
            return
        }
        do {
            let replacement = try FixtureLogger()
            logger?.write("fixtureRunEnded", details: ["reason": "manual_reset", "nextRunID": replacement.runID])
            logger = replacement
            counter = 0
            ticks = 0
            counterPaused = false
            lastAction = "No action observed yet."
            lastLayoutData = nil
            logger?.write("fixtureStarted", details: [
                "reason": "manual_reset", "operatingSystem": ProcessInfo.processInfo.operatingSystemVersionString,
                "pid": ProcessInfo.processInfo.processIdentifier,
                "counterPeriodSeconds": 1, "itemIDs": items.map { $0.id }, "axIDs": items.map { $0.axID }
            ])
            updateCounterAppearance()
            recordLayout(reason: "reset", force: true)
            updateControlLabels()
        } catch {
            showError("Could not start a new run", error.localizedDescription)
        }
    }

    @objc private func snapshotLayout(_ sender: Any?) {
        recordLayout(reason: "manual_snapshot", force: true)
        updateControlLabels()
    }

    @objc private func exportLog(_ sender: Any?) {
        guard let logger = logger else { return }
        do {
            logger.write("exportSnapshotRequested")
            let data = try logger.snapshot()
            let panel = NSSavePanel()
            panel.nameFieldStringValue = logger.fileURL.lastPathComponent
            panel.canCreateDirectories = true
            panel.isExtensionHidden = false
            if panel.runModal() == .OK, let url = panel.url {
                try data.write(to: url, options: .atomic)
            }
        } catch {
            showError("Could not export log", error.localizedDescription)
        }
    }

    @objc private func revealLog(_ sender: Any?) {
        guard let url = logger?.fileURL else { return }
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }

    @objc private func hideControls(_ sender: Any?) { controlWindow?.orderOut(nil) }
    @objc private func quitFixture(_ sender: Any?) { NSApp.terminate(nil) }

    private func showError(_ title: String, _ message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.runModal()
    }
}

let application = NSApplication.shared
let delegate = FixtureDelegate()
application.setActivationPolicy(.accessory)
application.delegate = delegate
application.run()

