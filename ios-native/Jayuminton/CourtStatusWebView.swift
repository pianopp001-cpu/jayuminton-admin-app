import SwiftUI
import WebKit
import UIKit

struct CourtStatusWebView: UIViewRepresentable {
    static let appVersion = "1.0.0"
    static let startURL = URL(string: "https://jayuminton-push.web.app/?mode=user&iosNative=1&nativeApp=1&appVersion=1.0.0")!

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        configuration.applicationNameForUserAgent = "JayumintonUserNativeIOS/\(Self.appVersion)"
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true

        let bridgeSource = Self.nativeBridgeJavaScript()
        configuration.userContentController.addUserScript(
            WKUserScript(source: bridgeSource, injectionTime: .atDocumentStart, forMainFrameOnly: false)
        )
        configuration.userContentController.add(context.coordinator, name: "nativeBridge")

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = true
        webView.scrollView.contentInsetAdjustmentBehavior = .automatic
        webView.isOpaque = false
        webView.backgroundColor = .systemBackground
        webView.scrollView.backgroundColor = .systemBackground

        var request = URLRequest(url: Self.startURL)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 20
        request.setValue("no-cache, no-store, must-revalidate", forHTTPHeaderField: "Cache-Control")
        request.setValue("no-cache", forHTTPHeaderField: "Pragma")
        webView.load(request)
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    static func dismantleUIView(_ uiView: WKWebView, coordinator: Coordinator) {
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: "nativeBridge")
        uiView.navigationDelegate = nil
        uiView.uiDelegate = nil
    }

    private static func nativeBridgeJavaScript() -> String {
        """
        (function(){
          window.__JAYUMINTON_USER_IOS_NATIVE__ = true;
          window.__JAYUMINTON_NATIVE_APP__ = true;
          window.__JAYUMINTON_NATIVE_APP_VERSION__ = '\(appVersion)';
          window.__JAYUMINTON_NATIVE_FCM__ = false;
          document.documentElement.setAttribute('data-user-ios-native','1');
          document.documentElement.setAttribute('data-native-app','1');

          function send(action, payload) {
            try {
              window.webkit.messageHandlers.nativeBridge.postMessage({action:action,payload:payload||{}});
            } catch (error) {}
          }

          window.NativeUserApp = {
            isInstalled: function(){ return true; },
            getVersion: function(){ return '\(appVersion)'; },
            hasNativeFcm: function(){ return false; },
            setMember: function(memberId, memberName){
              send('setMember',{memberId:String(memberId||''),memberName:String(memberName||'')});
            },
            clearMember: function(){ send('clearMember',{}); },
            setPushEnabled: function(enabled){ send('setPushEnabled',{enabled:!!enabled}); },
            setVibrationEnabled: function(enabled){ send('setVibrationEnabled',{enabled:!!enabled}); }
          };
        })();
        """
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
        private let allowedHost = "jayuminton-push.web.app"

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == "nativeBridge",
                  let body = message.body as? [String: Any],
                  let action = body["action"] as? String else { return }

            let payload = body["payload"] as? [String: Any] ?? [:]
            let defaults = UserDefaults.standard

            switch action {
            case "setMember":
                defaults.set(String(describing: payload["memberId"] ?? ""), forKey: "jayuminton.memberId")
                defaults.set(String(describing: payload["memberName"] ?? ""), forKey: "jayuminton.memberName")
            case "clearMember":
                defaults.removeObject(forKey: "jayuminton.memberId")
                defaults.removeObject(forKey: "jayuminton.memberName")
            case "setPushEnabled":
                defaults.set((payload["enabled"] as? Bool) ?? true, forKey: "jayuminton.pushEnabled")
            case "setVibrationEnabled":
                defaults.set((payload["enabled"] as? Bool) ?? true, forKey: "jayuminton.vibrationEnabled")
            default:
                break
            }
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            webView.evaluateJavaScript(CourtStatusWebView.nativeBridgeJavaScript())
        }

        func webView(_ webView: WKWebView,
                     decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }

            if url.scheme == "about" {
                decisionHandler(.allow)
                return
            }

            if url.scheme == "https", url.host == allowedHost {
                decisionHandler(.allow)
                return
            }

            if url.scheme == "http" || url.scheme == "https" {
                UIApplication.shared.open(url)
                decisionHandler(.cancel)
                return
            }

            if UIApplication.shared.canOpenURL(url) {
                UIApplication.shared.open(url)
            }
            decisionHandler(.cancel)
        }

        func webView(_ webView: WKWebView,
                     createWebViewWith configuration: WKWebViewConfiguration,
                     for navigationAction: WKNavigationAction,
                     windowFeatures: WKWindowFeatures) -> WKWebView? {
            if let url = navigationAction.request.url {
                if url.scheme == "https", url.host == allowedHost {
                    webView.load(navigationAction.request)
                } else if UIApplication.shared.canOpenURL(url) {
                    UIApplication.shared.open(url)
                }
            }
            return nil
        }
    }
}
