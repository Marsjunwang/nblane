// Native compositor / resize checks for the disposable macOS smoke instance.
import CoreGraphics
import Foundation

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

let arguments = Array(CommandLine.arguments.dropFirst())
if arguments == ["capture-access"] {
    guard CGPreflightScreenCaptureAccess() else {
        fail("The macOS CI runner lacks screen capture access; compositor verification cannot use a DOM screenshot substitute.")
    }
    exit(0)
}

guard arguments.count == 5, arguments[0] == "drag",
      let x = Double(arguments[1]), let y = Double(arguments[2]),
      let endX = Double(arguments[3]), let endY = Double(arguments[4]),
      [x, y, endX, endY].allSatisfy({ $0.isFinite }) else {
    fail("Usage: native-material capture-access | drag <x> <y> <end-x> <end-y>")
}
guard CGPreflightPostEventAccess() else {
    fail("The macOS CI runner lacks native event posting access; resize verification cannot use setBounds instead.")
}
guard let source = CGEventSource(stateID: .hidSystemState) else {
    fail("Could not create the Quartz event source")
}
func post(_ type: CGEventType, _ point: CGPoint) {
    guard let event = CGEvent(mouseEventSource: source, mouseType: type,
                              mouseCursorPosition: point, mouseButton: .left) else {
        fail("Could not create the Quartz pointer event")
    }
    event.setIntegerValueField(.mouseEventClickState, value: 1)
    event.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.06)
}
let start = CGPoint(x: x, y: y)
post(.mouseMoved, start)
post(.leftMouseDown, start)
for step in 1...12 {
    let fraction = Double(step) / 12
    post(.leftMouseDragged, CGPoint(x: x + (endX - x) * fraction,
                                   y: y + (endY - y) * fraction))
}
post(.leftMouseUp, CGPoint(x: endX, y: endY))
