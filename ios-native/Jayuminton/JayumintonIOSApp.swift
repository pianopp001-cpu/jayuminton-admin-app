import SwiftUI

@main
struct JayumintonIOSApp: App {
    var body: some Scene {
        WindowGroup {
            ZStack {
                Color.white.ignoresSafeArea()
                CourtStatusWebView()
            }
        }
    }
}
