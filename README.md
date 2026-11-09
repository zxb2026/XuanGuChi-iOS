# 竞价选股池 · iOS

桌面版 `竞价选股池 v1.0.0` 的 iPhone 壳工程。手机端逻辑沿用包内 `www/index.html`
（与安卓版同一份网页），iOS 侧只做一层原生壳：

```
WKWebView  ←  xgc://local/index.html      包内网页（选股/自选池/训练逻辑全在这里）
     │
     └── fetch xgc://local/__proxy?url=…  原生 WKURLSchemeHandler 转发到东财接口
```

安卓壳用 `shouldInterceptRequest` 代理 `https://proxy.local/fetch?url=` 绕开跨域；
iOS 用自定义 scheme 的 `WKURLSchemeHandler` 做同一件事，页面与代理同属 `xgc://local`
这一个源，因此不存在跨域问题。

## 目录

```
ios/XuanGuChi/                 Swift 源码 + Info.plist + Assets.xcassets + www/
ios/XuanGuChi.xcodeproj/       由 scripts/gen_ios_project.py 生成（勿手改）
scripts/gen_ios_icon.py        纯标准库生成 1024 图标（CI 上无 PIL 也能跑）
scripts/gen_ios_project.py     生成 pbxproj / workspace / shared scheme
scripts/build_unsigned_ipa.sh  xcodebuild 编译并打包未签名 IPA
.github/workflows/build-ipa.yml  macOS 云端编译流水线
```

## 本机（Windows）无法编译

iOS 包必须由 Xcode 编译，Windows 没有 xcodebuild。构建走 GitHub Actions 的
`macos-15` runner：推送即编译，产物是未签名 IPA（`XuanGuChi-unsigned.ipa`）。
安装需在 Windows 用 Sideloadly + 免费 Apple ID 重签；免费签名 7 天有效。

## 配置

- Bundle ID `com.xuanguchi.app`
- 显示名 `竞价选股池`，1.0.0 (1)，最低 iOS 15.0，仅 iPhone 竖屏
- 无第三方依赖，纯 UIKit + WebKit

## 风险说明

- 行情来自东方财富公开接口，接口频控/失败由网页层已有的异常降级处理。
- 本 App 仅用于本地复盘与初选研究，不构成投资建议，不自动交易。
