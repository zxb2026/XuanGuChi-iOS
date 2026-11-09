//
//  WebSchemeHandler.swift
//  竞价选股池 iOS
//
//  与安卓壳 MainActivity.shouldInterceptRequest 等价的原生代理层。
//
//  约定：
//    xgc://local/index.html        → 从 App 包内 www/ 目录读文件
//    xgc://local/__proxy?url=XXX  → 由原生层发起请求转发（绕开浏览器跨域限制）
//
//  两者同属 xgc://local 这个源，所以网页里 fetch() 属于同源请求，
//  CORS 完全不参与；网页逻辑与安卓版逐字一致，只替换了 PROXY 常量。
//

import Foundation
import WebKit

final class WebSchemeHandler: NSObject, WKURLSchemeHandler {

    static let scheme = "xgc"
    static let host = "local"
    static let proxyPath = "/__proxy"

    private let lock = NSLock()
    private var activeTasks: [ObjectIdentifier: URLSessionDataTask] = [:]
    private let session: URLSession

    override init() {
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 20
        cfg.timeoutIntervalForResource = 45
        cfg.requestCachePolicy = .reloadIgnoringLocalCacheData
        cfg.httpMaximumConnectionsPerHost = 8
        session = URLSession(configuration: cfg)
        super.init()
    }

    // MARK: - WKURLSchemeHandler

    func webView(_ webView: WKWebView, start urlSchemeTask: WKURLSchemeTask) {
        guard let url = urlSchemeTask.request.url else {
            fail(urlSchemeTask, code: 400, message: "bad url")
            return
        }
        if url.path == WebSchemeHandler.proxyPath {
            handleProxy(url, urlSchemeTask)
        } else {
            serveBundledFile(url, urlSchemeTask)
        }
    }

    func webView(_ webView: WKWebView, stop urlSchemeTask: WKURLSchemeTask) {
        let key = ObjectIdentifier(urlSchemeTask as AnyObject)
        lock.lock()
        let task = activeTasks.removeValue(forKey: key)
        lock.unlock()
        task?.cancel()
    }

    // MARK: - 包内静态资源

    private func serveBundledFile(_ url: URL, _ task: WKURLSchemeTask) {
        guard let resourceRoot = Bundle.main.resourceURL else {
            fail(task, code: 500, message: "bundle missing")
            return
        }
        let base = resourceRoot.appendingPathComponent("www", isDirectory: true)

        var relative = url.path
        if relative.isEmpty || relative == "/" { relative = "/index.html" }
        while relative.hasPrefix("/") { relative = String(relative.dropFirst()) }
        if relative.hasSuffix("/") { relative += "index.html" }

        let target = base.appendingPathComponent(relative)
        // 防目录穿越：解析后的路径必须仍在 www 目录内
        let normalized = target.standardizedFileURL.path
        let basePath = base.standardizedFileURL.path
        guard normalized.hasPrefix(basePath) else {
            fail(task, code: 403, message: "forbidden")
            return
        }
        guard let data = try? Data(contentsOf: target) else {
            fail(task, code: 404, message: "not found: \(relative)")
            return
        }

        let mime = WebSchemeHandler.mimeType(for: (relative as NSString).pathExtension)
        let headers = [
            "Content-Type": mime,
            "Content-Length": String(data.count),
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store"
        ]
        guard let response = HTTPURLResponse(url: url, statusCode: 200,
                                             httpVersion: "HTTP/1.1",
                                             headerFields: headers) else {
            fail(task, code: 500, message: "response build failed")
            return
        }
        task.didReceive(response)
        task.didReceive(data)
        task.didFinish()
    }

    // MARK: - 行情接口代理

    private func handleProxy(_ url: URL, _ task: WKURLSchemeTask) {
        let comps = URLComponents(url: url, resolvingAgainstBaseURL: false)
        guard let raw = comps?.queryItems?.first(where: { $0.name == "url" })?.value,
              let targetURL = URL(string: raw),
              let scheme = targetURL.scheme?.lowercased(),
              scheme == "http" || scheme == "https" else {
            fail(task, code: 400, message: "bad proxy target")
            return
        }

        var request = URLRequest(url: targetURL)
        request.timeoutInterval = 20
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                         forHTTPHeaderField: "User-Agent")
        request.setValue("https://quote.eastmoney.com/", forHTTPHeaderField: "Referer")
        request.setValue("application/json, text/plain, */*", forHTTPHeaderField: "Accept")

        let key = ObjectIdentifier(task as AnyObject)
        let dataTask = session.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self else { return }
            // WKURLSchemeTask 的回调统一回主线程，避免在后台线程操作 WebKit 对象
            DispatchQueue.main.async {
                self.lock.lock()
                let stillActive = self.activeTasks.removeValue(forKey: key) != nil
                self.lock.unlock()
                guard stillActive else { return }   // 已被 stop，不能再回调，否则 WebKit 抛异常

                if let error = error {
                    self.fail(task, code: 599, message: error.localizedDescription)
                    return
                }
                let http = response as? HTTPURLResponse
                let body = data ?? Data()
                let status = http?.statusCode ?? 200
                let mime = http?.mimeType ?? "application/json"
                let headers = [
                    "Content-Type": mime,
                    "Content-Length": String(body.count),
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "no-store"
                ]
                guard let resp = HTTPURLResponse(url: url, statusCode: status,
                                                 httpVersion: "HTTP/1.1",
                                                 headerFields: headers) else {
                    self.fail(task, code: 500, message: "response build failed")
                    return
                }
                task.didReceive(resp)
                task.didReceive(body)
                task.didFinish()
            }
        }

        lock.lock()
        activeTasks[key] = dataTask
        lock.unlock()
        dataTask.resume()
    }

    // MARK: - 工具

    private func fail(_ task: WKURLSchemeTask, code: Int, message: String) {
        let safe = message.replacingOccurrences(of: "\"", with: "'")
        let body = "{\"error\":\"\(safe)\"}".data(using: .utf8) ?? Data()
        let url = task.request.url ?? URL(string: "\(WebSchemeHandler.scheme)://\(WebSchemeHandler.host)/")!
        let headers = [
            "Content-Type": "application/json",
            "Content-Length": String(body.count),
            "Access-Control-Allow-Origin": "*"
        ]
        guard let resp = HTTPURLResponse(url: url, statusCode: code,
                                         httpVersion: "HTTP/1.1",
                                         headerFields: headers) else { return }
        task.didReceive(resp)
        task.didReceive(body)
        task.didFinish()
    }

    static func mimeType(for ext: String) -> String {
        switch ext.lowercased() {
        case "html", "htm": return "text/html"
        case "js":          return "text/javascript"
        case "css":         return "text/css"
        case "json":        return "application/json"
        case "png":         return "image/png"
        case "jpg", "jpeg": return "image/jpeg"
        case "svg":         return "image/svg+xml"
        case "woff2":       return "font/woff2"
        default:            return "application/octet-stream"
        }
    }
}
