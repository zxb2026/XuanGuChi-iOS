#!/usr/bin/env bash
# 编译「未签名真机 IPA」，供 Windows 侧用免费 Apple ID 重签安装。
#
#   ./scripts/build_unsigned_ipa.sh
#     → ios/build/export/XuanGuChi-unsigned.ipa
#
# 只能在 macOS（本机或 GitHub Actions 的 macos runner）上运行：
# Windows 没有 xcodebuild，无法编译 iOS App。
# 不需要付费开发者账号、不需要证书、不需要设备 UDID、不需要任何 Secrets。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IOS="$ROOT/ios"
PROJECT="$IOS/XuanGuChi.xcodeproj"
SCHEME="XuanGuChi"
APP_NAME="XuanGuChi"
DD="$IOS/build/UnsignedDerivedData"
STAGE="$IOS/build/ipa-stage"
OUT="$IOS/build/export/XuanGuChi-unsigned.ipa"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "错误：只能在 macOS / GitHub Actions 的 macOS runner 上运行（当前 $(uname -s)）。" >&2
  exit 3
fi
command -v xcodebuild >/dev/null || {
  echo "错误：未找到 xcodebuild，请先执行 sudo xcode-select -s /Applications/Xcode.app/Contents/Developer" >&2
  exit 3
}

echo "==> 0/4 预检：工程与资源"
test -f "$PROJECT/project.pbxproj" || { echo "错误：缺少 $PROJECT/project.pbxproj（先跑 scripts/gen_ios_project.py）" >&2; exit 4; }
test -f "$IOS/$APP_NAME/www/index.html" || { echo "错误：缺少网页资源 www/index.html" >&2; exit 4; }
test -f "$IOS/$APP_NAME/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png" || {
  echo "错误：缺少 1024 图标（先跑 scripts/gen_ios_icon.py）" >&2; exit 4; }

echo "==> 1/4 编译真机 arm64 版本（不签名）"
mkdir -p "$DD" "$STAGE" "$(dirname "$OUT")"
rm -rf "$STAGE/Payload"
xcodebuild -project "$PROJECT" -scheme "$SCHEME" -configuration Release \
  -destination 'generic/platform=iOS' -derivedDataPath "$DD" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" \
  clean build

APP="$DD/Build/Products/Release-iphoneos/$APP_NAME.app"
if [[ ! -d "$APP" ]]; then
  echo "错误：编译结束但没找到 $APP_NAME.app，检查 $DD/Build/Products" >&2
  ls -R "$DD/Build/Products" 2>/dev/null | head -n 60 || true
  exit 4
fi

echo "==> 2/4 打包成标准 Payload 结构"
mkdir -p "$STAGE/Payload"
cp -R "$APP" "$STAGE/Payload/"
rm -f "$OUT"
(cd "$STAGE" && zip -qry "$OUT" Payload)

echo "==> 3/4 校验产物"
if [[ ! -s "$OUT" ]]; then
  echo "错误：IPA 未生成或为空：$OUT" >&2; exit 5
fi
fail=0
unzip -Z1 "$OUT" | grep -q "^Payload/$APP_NAME.app/Info.plist$" || { echo "✗ 缺 Info.plist"; fail=1; }
unzip -Z1 "$OUT" | grep -q "^Payload/$APP_NAME.app/www/index.html$" || { echo "✗ 缺 www/index.html"; fail=1; }
unzip -Z1 "$OUT" | grep -q "^Payload/$APP_NAME.app/Assets.car$" || { echo "✗ 缺 Assets.car（图标未编译）"; fail=1; }
if [[ $fail -ne 0 ]]; then
  echo "错误：产物结构不合规" >&2; exit 5
fi

BIN="$STAGE/Payload/$APP_NAME.app/$APP_NAME"
echo "    可执行文件：$(file -b "$BIN")"
echo "    Bundle ID   ：$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Info.plist")"
echo "    显示名      ：$(/usr/libexec/PlistBuddy -c 'Print :CFBundleDisplayName' "$APP/Info.plist")"
echo "    版本        ：$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Info.plist") ($(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$APP/Info.plist"))"
echo "    最低 iOS    ：$(/usr/libexec/PlistBuddy -c 'Print :MinimumOSVersion' "$APP/Info.plist" 2>/dev/null || echo "$(plutil -extract MinimumOSVersion raw "$APP/Info.plist" 2>/dev/null || echo -)")"
echo "    包大小      ：$(du -h "$OUT" | awk '{print $1}')"

echo "✅ 未签名 IPA：$OUT"
