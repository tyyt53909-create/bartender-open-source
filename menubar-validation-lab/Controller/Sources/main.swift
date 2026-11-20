import AppKit

// Research controller: changes only its own NSStatusItems.
// No automatic sorting, cross-app input, menu-session lease or private assertion.
final class LabController: NSObject, NSApplicationDelegate {
    private var spacers: [NSStatusItem] = []
    private var control: NSStatusItem?
    private var window: NSWindow?
    private var statusLabel: NSTextField?
    private var logView: NSTextView?
    private var logHandle: FileHandle?
    private var logURL: URL?
    private var logBytes = 0
    private let logLimit = 8 * 1024 * 1024
    private let runID = UUID().uuidString
    private var generation = 0
    private var active = false
    private var experimentTimer: Timer?
    private var pendingTimer: Timer?
    private var observers: [NSObjectProtocol] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        prepareLog()
        makeApplicationMenu()
        makeWindow()
        for index in 0...CandidateGeometry.spacerCount {
            let item = NSStatusBar.system.statusItem(withLength: index == 0 ? 20 : 0)
            item.autosaveName = "MenuValidation.Spacer.\(index)"
            item.button?.title = index == 0 ? "|" : ""
            item.button?.toolTip = "Lab spacer \(index)"
            spacers.append(item)
        }
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        item.autosaveName = "MenuValidation.Control"
        item.button?.title = "LAB"
        item.button?.toolTip = "Menu Bar Validation Lab"
        let menu = NSMenu()
        menu.addItem(action("立即展开", #selector(restorePressed), key: ""))
        menu.addItem(action("显示实验窗口", #selector(showWindow), key: ""))
        menu.addItem(.separator())
        menu.addItem(action("退出实验", #selector(quit), key: "q"))
        item.menu = menu
        control = item
        observeChanges()
        record("controller_started", [
            "backend": "guarded_candidate",
            "os": ProcessInfo.processInfo.operatingSystemVersionString,
            "screens": Diagnostics.screens(),
            "private_assertion_enabled": false,
            "menu_session_guard": "not_implemented"
        ])
        setStatus("尚未收起。先完成无管理器基线，再手动放置 0–6 定位标记。")
        showWindow()
    }

    private func prepareLog() {
        do {
            let support = try FileManager.default.url(for: .applicationSupportDirectory,
                                                       in: .userDomainMask, appropriateFor: nil,
                                                       create: true)
            let directory = support.appendingPathComponent("MenuBarValidationLab/Controller", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            let url = directory.appendingPathComponent("controller-\(runID).jsonl")
            guard FileManager.default.createFile(atPath: url.path, contents: nil) else { return }
            logHandle = try FileHandle(forWritingTo: url)
            logURL = url
        } catch { logHandle = nil }
    }

    private func action(_ title: String, _ selector: Selector, key: String) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: selector, keyEquivalent: key)
        item.target = self
        return item
    }

    private func makeApplicationMenu() {
        let main = NSMenu()
        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        let restore = action("立即展开", #selector(restorePressed), key: "r")
        restore.keyEquivalentModifierMask = [.command, .shift]
        appMenu.addItem(restore)
        appMenu.addItem(action("显示实验窗口", #selector(showWindow), key: ""))
        appMenu.addItem(.separator())
        appMenu.addItem(action("退出实验", #selector(quit), key: "q"))
        appItem.submenu = appMenu
        main.addItem(appItem)
        NSApp.mainMenu = main
    }

    private func makeWindow() {
        let w = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 790, height: 560),
                         styleMask: [.titled, .closable, .miniaturizable, .resizable],
                         backing: .buffered, defer: false)
        w.title = "Menu Bar Validation Lab — geometry experiment"
        w.isReleasedWhenClosed = false
        w.center()
        let body = NSView()
        w.contentView = body
        let title = NSTextField(labelWithString: "菜单栏几何验证")
        title.font = .systemFont(ofSize: 20, weight: .semibold)
        let instructions = NSTextField(wrappingLabelWithString:
            "此原型只改变自己的占位项。先显示定位标记，再用 Command 拖动，让 0–6 连续位于待测图标右侧、LAB 左侧。每次收起最多计划维持 10 秒；屏幕变化时请求展开。定时器不保证主线程卡死时恢复。")
        let status = NSTextField(wrappingLabelWithString: "")
        status.font = .systemFont(ofSize: 13, weight: .medium)
        statusLabel = status
        let row = NSStackView()
        row.orientation = .horizontal
        row.spacing = 8
        let buttons: [(String, Selector)] = [
            ("显示定位标记", #selector(markersPressed)),
            ("收起 10 秒", #selector(collapsePressed)),
            ("5 秒后收起", #selector(schedulePressed)),
            ("立即展开", #selector(restorePressed))
        ]
        for (label, selector) in buttons { row.addArrangedSubview(NSButton(title: label, target: self, action: selector)) }
        let second = NSStackView()
        second.orientation = .horizontal
        second.spacing = 8
        second.addArrangedSubview(NSButton(title: "展开后导出快照", target: self, action: #selector(exportSnapshot)))
        second.addArrangedSubview(NSButton(title: "查看日志", target: self, action: #selector(revealLog)))
        second.addArrangedSubview(NSButton(title: "隐藏窗口", target: self, action: #selector(hideWindow)))
        let limits = NSTextField(wrappingLabelWithString:
            "仅 macOS 26 / 27 开放几何实验；27 会拒绝容量不足或余量不足的模型。未实现单项搜索、三分区、转发点击、规则引擎或菜单会话锁。5 秒延迟仅用于注入试验触发。日志记录命令，不证明收起成功。")
        limits.textColor = .secondaryLabelColor
        let scroll = NSScrollView()
        scroll.hasVerticalScroller = true
        scroll.borderType = .bezelBorder
        let text = NSTextView(frame: NSRect(x: 0, y: 0, width: 740, height: 220))
        text.isEditable = false
        text.font = .monospacedSystemFont(ofSize: 11, weight: .regular)
        text.isVerticallyResizable = true
        text.isHorizontallyResizable = false
        text.autoresizingMask = [.width]
        text.textContainer?.widthTracksTextView = true
        scroll.documentView = text
        logView = text
        let stack = NSStackView(views: [title, instructions, row, second, status, limits, scroll])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        body.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: body.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: body.trailingAnchor, constant: -20),
            stack.topAnchor.constraint(equalTo: body.topAnchor, constant: 20),
            stack.bottomAnchor.constraint(equalTo: body.bottomAnchor, constant: -20),
            scroll.widthAnchor.constraint(equalTo: stack.widthAnchor),
            scroll.heightAnchor.constraint(greaterThanOrEqualToConstant: 180),
            instructions.widthAnchor.constraint(equalTo: stack.widthAnchor),
            limits.widthAnchor.constraint(equalTo: stack.widthAnchor),
            status.widthAnchor.constraint(equalTo: stack.widthAnchor)
        ])
        w.minSize = NSSize(width: 790, height: 560)
        window = w
    }

    private func observeChanges() {
        observers.append(NotificationCenter.default.addObserver(
            forName: NSApplication.didChangeScreenParametersNotification, object: nil, queue: .main
        ) { [weak self] _ in
            self?.restore(reason: "screen_topology_changed")
            self?.record("screen_topology_observed", ["screens": Diagnostics.screens()])
            self?.setStatus("屏幕配置已变化，已请求展开；请重新记录拓扑和排列。")
        })
        for name in [NSWorkspace.willSleepNotification, NSWorkspace.sessionDidResignActiveNotification] {
            observers.append(NSWorkspace.shared.notificationCenter.addObserver(
                forName: name, object: nil, queue: .main
            ) { [weak self] _ in
                self?.restore(reason: "sleep_or_session_inactive")
                self?.setStatus("休眠或会话切换，已请求展开。")
            })
        }
    }

    @discardableResult private func record(_ event: String, _ details: [String: Any] = [:]) -> Bool {
        let entry: [String: Any] = [
            "schema_version": 1, "event": event, "timestamp": Diagnostics.timestamp(),
            "monotonic_seconds": ProcessInfo.processInfo.systemUptime,
            "controller_run_id": runID, "generation": generation, "active_command": active,
            "evidence_level": "machine_observation_not_task_verdict", "details": details
        ]
        guard let data = try? JSONSerialization.data(withJSONObject: entry, options: [.sortedKeys]),
              let handle = logHandle, logBytes + data.count + 1 <= logLimit else {
            return false
        }
        do {
            try handle.write(contentsOf: data)
            try handle.write(contentsOf: Data([10]))
            logBytes += data.count + 1
            if let line = String(data: data, encoding: .utf8), let view = logView {
                var lines = view.string.components(separatedBy: "\n")
                lines.append(line)
                view.string = lines.suffix(120).joined(separator: "\n")
                view.scrollToEndOfDocument(nil)
            }
            return true
        } catch {
            try? logHandle?.close()
            logHandle = nil
            return false
        }
    }

    private func setStatus(_ text: String) { statusLabel?.stringValue = text }

    @objc private func showWindow() {
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    @objc private func hideWindow() { window?.orderOut(nil) }
    @objc private func markersPressed() {
        restore(reason: "show_markers")
        for (index, spacer) in spacers.enumerated() {
            spacer.length = 22
            spacer.button?.title = "\(index)"
        }
        record("position_markers_shown", ["placement": "manual_only_not_verified"])
        setStatus("请手动放置 0–6；连续放在待测图标右侧、LAB 左侧。记录拖动后的基线。")
    }
    @objc private func collapsePressed() { collapse() }
    @objc private func schedulePressed() {
        restore(reason: "schedule_new_experiment")
        guard logHandle != nil, logBytes < logLimit - 32768 else {
            setStatus("无法完整记录日志，拒绝安排实验。"); return
        }
        let ticket = generation
        let timer = Timer(timeInterval: 5, repeats: false) { [weak self] _ in
            guard let self = self, self.generation == ticket else { return }
            self.pendingTimer = nil
            self.collapse()
        }
        pendingTimer = timer
        addTimer(timer)
        record("collapse_scheduled", ["delay_seconds": 5, "rule_engine": "not_implemented"])
        setStatus("5 秒后请求收起。现在可隐藏窗口并打开 Fixture 菜单，观察是否被打断。")
    }

    private func addTimer(_ timer: Timer) {
        RunLoop.main.add(timer, forMode: .common)
        RunLoop.main.add(timer, forMode: .eventTracking)
        RunLoop.main.add(timer, forMode: .modalPanel)
    }

    private func collapse() {
        // Refuse new layout changes before restoring or resizing any item.
        if NSEvent.pressedMouseButtons != 0 {
            record("collapse_refused", ["reason": "mouse_button_currently_down",
                                        "new_layout_mutation": false])
            setStatus("鼠标仍按下，拒绝本次新收起；已有实验的到期恢复仍可能执行。"); return
        }
        restore(reason: "replace_experiment")
        guard logHandle != nil, logBytes < logLimit - 32768 else {
            setStatus("日志不可用或接近上限，拒绝开始实验。"); return
        }
        let major = ProcessInfo.processInfo.operatingSystemVersion.majorVersion
        var details: [String: Any] = [
            "menu_session_guard": "not_implemented", "visibility_verified": false,
            "planned_retract_after_seconds": 10, "generation_invalidates_pending_work": true
        ]
        var widths = Array(repeating: CGFloat(0), count: spacers.count)
        if major == 26 {
            widths[0] = 10_000
            details["strategy"] = "legacy_single_spacer_experiment"
            details["validation_status"] = "not_verified_on_this_machine"
        } else if major == 27 {
            let screens = NSScreen.screens
            var inputs: [DisplayGeometry] = []
            for screen in screens {
                if screen.safeAreaInsets.top > 0 {
                    guard let right = screen.auxiliaryTopRightArea, right.width > 0 else {
                        record("collapse_refused", ["reason": "notch_status_area_unknown"])
                        setStatus("缺少刘海右侧区域数据，拒绝猜测占位宽度。"); return
                    }
                    inputs.append(DisplayGeometry(width: Double(screen.frame.width), statusWidth: Double(right.width)))
                } else {
                    inputs.append(DisplayGeometry(width: Double(screen.frame.width), statusWidth: Double(screen.frame.width)))
                }
            }
            let plan = CandidateGeometry.plan(inputs)
            details["geometry_plan"] = plan.json
            guard plan.allowed else {
                record("collapse_refused", details)
                setStatus("几何模型拒绝实验：\(plan.reason)。该拒绝不是隐藏功能通过。"); return
            }
            for index in 0...plan.activeSpacers { widths[index] = CGFloat(plan.unit) }
            details["strategy"] = "guarded_native_overflow"
        } else {
            record("collapse_refused", ["reason": "os_outside_experiment_scope", "major": major])
            setStatus("当前系统仅开放观察；收起实验限定为 macOS 26 / 27。"); return
        }
        guard record("collapse_request_accepted", details) else {
            setStatus("写入实验记录失败，保持展开。"); return
        }
        generation += 1
        active = true
        let ticket = generation
        // Start the deadline before mutations; this still cannot protect against main-thread stalls.
        let timer = Timer(timeInterval: 10, repeats: false) { [weak self] _ in
            guard let self = self, self.generation == ticket else { return }
            self.restore(reason: "ten_second_deadline")
            self.setStatus("10 秒实验结束，已请求展开。请依据真实显示和 Fixture 日志判定。")
        }
        experimentTimer = timer
        addTimer(timer)
        for (index, spacer) in spacers.enumerated() {
            spacer.button?.title = ""
            spacer.length = widths[index]
        }
        guard record("own_lengths_assigned", ["widths_points": widths.map { Double($0) },
                                              "actual_visibility": "unknown"]) else {
            restore(reason: "recording_interrupted_after_mutation")
            setStatus("记录中断，已请求展开；本次证据不完整，不能判为通过。"); return
        }
        setStatus("已赋予占位宽度，10 秒后请求展开；实际隐藏、目标与菜单行为须另行观察。")
    }

    private func restore(reason: String) {
        generation += 1
        experimentTimer?.invalidate()
        experimentTimer = nil
        pendingTimer?.invalidate()
        pendingTimer = nil
        active = false
        for (index, spacer) in spacers.enumerated() {
            spacer.length = index == 0 ? 20 : 0
            spacer.button?.title = index == 0 ? "|" : ""
        }
        record("restore_requested", [
            "reason": reason, "scope": "only_own_status_item_lengths",
            "other_app_order_restored": false, "actual_visibility": "unknown"
        ])
    }
    @objc private func restorePressed() {
        restore(reason: "operator_requested")
        setStatus("已请求展开。仅恢复本程序自己的占位宽度，未写入其他应用的顺序。")
    }
    @objc private func exportSnapshot() {
        restore(reason: "expanded_snapshot")
        var snapshot = Diagnostics.snapshot()
        snapshot["controller_run_id"] = runID
        snapshot["controller_state"] = "expanded_after_restore_request"
        guard let data = try? JSONSerialization.data(withJSONObject: snapshot, options: [.prettyPrinted, .sortedKeys]) else {
            setStatus("快照序列化失败。"); return
        }
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "expanded-snapshot-\(runID).json"
        if panel.runModal() == .OK, let url = panel.url {
            do {
                try data.write(to: url, options: .atomic)
                record("expanded_snapshot_exported", ["state": "expanded_after_restore_request"])
                setStatus("已导出展开请求后的观察快照；不包含收起状态。")
            } catch { setStatus("快照保存失败：\(error.localizedDescription)") }
        }
    }
    @objc private func revealLog() {
        if let url = logURL { NSWorkspace.shared.activateFileViewerSelecting([url]) }
        else { setStatus("日志文件不可用，不能开始实验。") }
    }
    @objc private func quit() { NSApp.terminate(nil) }
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        showWindow()
        return true
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }
    func applicationWillTerminate(_ notification: Notification) {
        restore(reason: "normal_termination")
        record("controller_stopping", ["crash_recovery_verified": false])
        for spacer in spacers { NSStatusBar.system.removeStatusItem(spacer) }
        if let control = control { NSStatusBar.system.removeStatusItem(control) }
        try? logHandle?.close()
    }
}

let app = NSApplication.shared
let delegate = LabController()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()

