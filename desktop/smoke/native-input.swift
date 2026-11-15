// Real Quartz events test NSWindow hit testing, including Electron drag regions.
import CoreGraphics
import Foundation

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

guard CGPreflightPostEventAccess() else {
    fail("Native input requires macOS Accessibility permission for the test runner. No DOM/CDP fallback is allowed.")
}
guard let source = CGEventSource(stateID: .hidSystemState) else {
    fail("Could not create the Quartz event source")
}
func post(_ event: CGEvent?) {
    guard let event = event else { fail("Could not create the Quartz event") }
    event.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.08)
}

let arguments = Array(CommandLine.arguments.dropFirst())
if arguments == ["escape"] {
    post(CGEvent(keyboardEventSource: source, virtualKey: 53, keyDown: true))
    post(CGEvent(keyboardEventSource: source, virtualKey: 53, keyDown: false))
} else if arguments.count == 3 && arguments[0] == "click",
          let x = Double(arguments[1]), let y = Double(arguments[2]), x.isFinite, y.isFinite {
    let point = CGPoint(x: x, y: y)
    post(CGEvent(mouseEventSource: source, mouseType: .mouseMoved,
                 mouseCursorPosition: point, mouseButton: .left))
    let down = CGEvent(mouseEventSource: source, mouseType: .leftMouseDown,
                       mouseCursorPosition: point, mouseButton: .left)
    down?.setIntegerValueField(.mouseEventClickState, value: 1)
    post(down)
    let up = CGEvent(mouseEventSource: source, mouseType: .leftMouseUp,
                     mouseCursorPosition: point, mouseButton: .left)
    up?.setIntegerValueField(.mouseEventClickState, value: 1)
    post(up)
} else {
    fail("Usage: native-input click <x> <y> | escape")
}
