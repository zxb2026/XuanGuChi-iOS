//
//  XuanGuChiApp.swift
//  竞价选股池 iOS
//
//  App 入口（UIKit 生命周期，不用 SwiftUI）：整个界面由 WebViewController 承载包内网页。
//  刻意不声明 UIScene，走传统 window 生命周期，安全区 inset 才是确定可预期的。
//

import UIKit

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {

    var window: UIWindow?

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.backgroundColor = UIColor(red: 0x12 / 255.0, green: 0x14 / 255.0,
                                         blue: 0x1a / 255.0, alpha: 1.0)
        window.rootViewController = WebViewController()
        window.makeKeyAndVisible()
        self.window = window
        return true
    }
}
