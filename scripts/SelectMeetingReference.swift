import AppKit
import UniformTypeIdentifiers

final class PickerDelegate: NSObject, NSApplicationDelegate {
func applicationDidFinishLaunching(_ notification: Notification) {
let app = NSApplication.shared
app.activate(ignoringOtherApps: true)
let panel = NSOpenPanel()
panel.title = "選擇本次 Google 詞彙表匯出"
panel.message = "請先在 Google 試算表選擇「檔案 → 下載 → Microsoft Excel」，再選擇本次檔案。工具不會自動使用舊快取。"
panel.prompt = "使用這份詞彙表"
panel.allowedContentTypes = [UTType(filenameExtension: "xlsx")!]
panel.allowsMultipleSelection = false
panel.canChooseDirectories = false
panel.directoryURL = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Downloads")
if panel.runModal() == .OK, let url = panel.url {
    guard CommandLine.arguments.count == 2 else { app.terminate(nil); return }
    try? url.path.write(toFile: CommandLine.arguments[1], atomically: true, encoding: .utf8)
}
app.terminate(nil)
}
}
let app = NSApplication.shared
let delegate = PickerDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
