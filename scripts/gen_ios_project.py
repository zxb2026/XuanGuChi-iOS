# -*- coding: utf-8 -*-
"""生成 Xcode 工程文件（project.pbxproj / workspace / shared scheme）。

运行：python scripts/gen_ios_project.py

工程形态：
  ios/XuanGuChi/            Swift 源码（扁平）
  ios/XuanGuChi/Info.plist  手写 Info.plist
  ios/XuanGuChi/Assets.xcassets
  ios/XuanGuChi/www/        以「文件夹引用」整目录拷进 App 包（网页 + 未来静态资源）

零第三方依赖、纯系统框架（UIKit / WebKit）；ID 由名字哈希生成，重复生成结果稳定。
"""
import hashlib
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

APP_NAME = "XuanGuChi"
SRC = os.path.join("ios", APP_NAME)
PROJ = os.path.join("ios", APP_NAME + ".xcodeproj")
BUNDLE_ID = "com.xuanguchi.app"
DEPLOY = "15.0"

TARGET_ID = "B7C1D2E3F4A50000000000A1"
PRODUCT_ID = "B7C1D2E3F4A50000000000A2"
PROJECT_ID = "B7C1D2E3F4A50000000000A3"
MAIN_GROUP_ID = "B7C1D2E3F4A50000000000A4"
APP_GROUP_ID = "B7C1D2E3F4A50000000000A5"
PRODUCTS_GROUP_ID = "B7C1D2E3F4A50000000000A6"
SOURCES_PHASE_ID = "B7C1D2E3F4A50000000000B1"
RESOURCES_PHASE_ID = "B7C1D2E3F4A50000000000B2"
FRAMEWORKS_PHASE_ID = "B7C1D2E3F4A50000000000B3"
PROJ_CFG_LIST_ID = "B7C1D2E3F4A50000000000C1"
TARGET_CFG_LIST_ID = "B7C1D2E3F4A50000000000C2"
PROJ_DEBUG_ID = "B7C1D2E3F4A50000000000C3"
PROJ_RELEASE_ID = "B7C1D2E3F4A50000000000C4"
TARGET_DEBUG_ID = "B7C1D2E3F4A50000000000C5"
TARGET_RELEASE_ID = "B7C1D2E3F4A50000000000C6"


def oid(name):
    return hashlib.sha1(name.encode("utf-8")).hexdigest()[:24].upper()


file_ref_ids, build_file_ids = {}, {}


def ref(entry):
    key = entry.replace("\\", "/")
    file_ref_ids.setdefault(key, oid("ref:" + key))
    return file_ref_ids[key]


def bf(entry, phase):
    key = phase + ":" + entry.replace("\\", "/")
    build_file_ids.setdefault(key, oid("bf:" + key))
    return build_file_ids[key]


def q(s):
    if s and all(c.isalnum() or c in "._-/" for c in s):
        return s
    return '"%s"' % s.replace('"', '\\"')


SWIFT = sorted(fn for fn in os.listdir(SRC) if fn.endswith(".swift"))
PLIST = "Info.plist"
ASSETS = "Assets.xcassets"
WWW = "www"

lines = []
a = lines.append
a("// !$*UTF8*$!")
a("{")
a("\tarchiveVersion = 1;")
a("\tclasses = {")
a("\t};")
a("\tobjectVersion = 56;")
a("\tobjects = {")

a("")
a("/* Begin PBXBuildFile section */")
for fn in SWIFT:
    a("\t\t%s /* %s in Sources */ = {isa = PBXBuildFile; fileRef = %s /* %s */; };" %
      (bf(fn, "src"), fn, ref(fn), fn))
a("\t\t%s /* Assets.xcassets in Resources */ = {isa = PBXBuildFile; fileRef = %s /* Assets.xcassets */; };" %
  (bf(ASSETS, "res"), ref(ASSETS)))
a("\t\t%s /* www in Resources */ = {isa = PBXBuildFile; fileRef = %s /* www */; };" %
  (bf(WWW, "res"), ref(WWW)))
a("\t\t%s /* %s.app in Products */ = {isa = PBXBuildFile; fileRef = %s /* %s.app */; };" %
  (oid("bf:product"), APP_NAME, PRODUCT_ID, APP_NAME))
a("/* End PBXBuildFile section */")

a("")
a("/* Begin PBXFileReference section */")
for fn in SWIFT:
    a("\t\t%s /* %s */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = %s; sourceTree = \"<group>\"; };" %
      (ref(fn), fn, q(fn)))
a("\t\t%s /* Info.plist */ = {isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = \"<group>\"; };" % ref(PLIST))
a("\t\t%s /* Assets.xcassets */ = {isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Assets.xcassets; sourceTree = \"<group>\"; };" % ref(ASSETS))
a("\t\t%s /* www */ = {isa = PBXFileReference; lastKnownFileType = folder; path = www; sourceTree = \"<group>\"; };" % ref(WWW))
a("\t\t%s /* %s.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = %s.app; sourceTree = BUILT_PRODUCTS_DIR; };" % (PRODUCT_ID, APP_NAME, APP_NAME))
a("/* End PBXFileReference section */")

a("")
a("/* Begin PBXFrameworksBuildPhase section */")
a("\t\t%s /* Frameworks */ = {" % FRAMEWORKS_PHASE_ID)
a("\t\t\tisa = PBXFrameworksBuildPhase;")
a("\t\t\tbuildActionMask = 2147483647;")
a("\t\t\tfiles = (")
a("\t\t\t);")
a("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
a("\t\t};")
a("/* End PBXFrameworksBuildPhase section */")

a("")
a("/* Begin PBXGroup section */")
a("\t\t%s = {" % MAIN_GROUP_ID)
a("\t\t\tisa = PBXGroup;")
a("\t\t\tchildren = (")
a("\t\t\t\t%s /* %s */," % (APP_GROUP_ID, APP_NAME))
a("\t\t\t\t%s /* Products */," % PRODUCTS_GROUP_ID)
a("\t\t\t);")
a("\t\t\tsourceTree = \"<group>\";")
a("\t\t};")
a("\t\t%s /* %s */ = {" % (APP_GROUP_ID, APP_NAME))
a("\t\t\tisa = PBXGroup;")
a("\t\t\tchildren = (")
a("\t\t\t\t%s /* Assets.xcassets */," % ref(ASSETS))
a("\t\t\t\t%s /* Info.plist */," % ref(PLIST))
a("\t\t\t\t%s /* www */," % ref(WWW))
for fn in SWIFT:
    a("\t\t\t\t%s /* %s */," % (ref(fn), fn))
a("\t\t\t);")
a("\t\t\tpath = %s;" % APP_NAME)
a("\t\t\tsourceTree = \"<group>\";")
a("\t\t};")
a("\t\t%s /* Products */ = {" % PRODUCTS_GROUP_ID)
a("\t\t\tisa = PBXGroup;")
a("\t\t\tchildren = (")
a("\t\t\t\t%s /* %s.app */," % (PRODUCT_ID, APP_NAME))
a("\t\t\t);")
a("\t\t\tname = Products;")
a("\t\t\tsourceTree = \"<group>\";")
a("\t\t};")
a("/* End PBXGroup section */")

a("")
a("/* Begin PBXNativeTarget section */")
a("\t\t%s /* %s */ = {" % (TARGET_ID, APP_NAME))
a("\t\t\tisa = PBXNativeTarget;")
a("\t\t\tbuildConfigurationList = %s /* Build configuration list for PBXNativeTarget \"%s\" */;" % (TARGET_CFG_LIST_ID, APP_NAME))
a("\t\t\tbuildPhases = (")
a("\t\t\t\t%s /* Sources */," % SOURCES_PHASE_ID)
a("\t\t\t\t%s /* Frameworks */," % FRAMEWORKS_PHASE_ID)
a("\t\t\t\t%s /* Resources */," % RESOURCES_PHASE_ID)
a("\t\t\t);")
a("\t\t\tbuildRules = (")
a("\t\t\t);")
a("\t\t\tdependencies = (")
a("\t\t\t);")
a("\t\t\tname = %s;" % APP_NAME)
a("\t\t\tproductName = %s;" % APP_NAME)
a("\t\t\tproductReference = %s /* %s.app */;" % (PRODUCT_ID, APP_NAME))
a("\t\t\tproductType = \"com.apple.product-type.application\";")
a("\t\t};")
a("/* End PBXNativeTarget section */")

a("")
a("/* Begin PBXProject section */")
a("\t\t%s /* Project object */ = {" % PROJECT_ID)
a("\t\t\tisa = PBXProject;")
a("\t\t\tattributes = {")
a("\t\t\t\tBuildIndependentTargetsInParallel = 1;")
a("\t\t\t\tLastUpgradeCheck = 1500;")
a("\t\t\t\tTargetAttributes = {")
a("\t\t\t\t\t%s = {" % TARGET_ID)
a("\t\t\t\t\t\tCreatedOnToolsVersion = 15.0;")
a("\t\t\t\t\t};")
a("\t\t\t\t};")
a("\t\t\t};")
a("\t\t\tbuildConfigurationList = %s /* Build configuration list for PBXProject \"%s\" */;" % (PROJ_CFG_LIST_ID, APP_NAME))
a("\t\t\tcompatibilityVersion = \"Xcode 14.0\";")
a("\t\t\tdevelopmentRegion = \"zh-Hans\";")
a("\t\t\thasScannedForEncodings = 0;")
a("\t\t\tknownRegions = (")
a("\t\t\t\ten,")
a("\t\t\t\tBase,")
a("\t\t\t\t\"zh-Hans\",")
a("\t\t\t);")
a("\t\t\tmainGroup = %s;" % MAIN_GROUP_ID)
a("\t\t\tproductRefGroup = %s /* Products */;" % PRODUCTS_GROUP_ID)
a("\t\t\tprojectDirPath = \"\";")
a("\t\t\tprojectRoot = \"\";")
a("\t\t\ttargets = (")
a("\t\t\t\t%s /* %s */," % (TARGET_ID, APP_NAME))
a("\t\t\t);")
a("\t\t};")
a("/* End PBXProject section */")

a("")
a("/* Begin PBXResourcesBuildPhase section */")
a("\t\t%s /* Resources */ = {" % RESOURCES_PHASE_ID)
a("\t\t\tisa = PBXResourcesBuildPhase;")
a("\t\t\tbuildActionMask = 2147483647;")
a("\t\t\tfiles = (")
a("\t\t\t\t%s /* Assets.xcassets in Resources */," % bf(ASSETS, "res"))
a("\t\t\t\t%s /* www in Resources */," % bf(WWW, "res"))
a("\t\t\t);")
a("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
a("\t\t};")
a("/* End PBXResourcesBuildPhase section */")

a("")
a("/* Begin PBXSourcesBuildPhase section */")
a("\t\t%s /* Sources */ = {" % SOURCES_PHASE_ID)
a("\t\t\tisa = PBXSourcesBuildPhase;")
a("\t\t\tbuildActionMask = 2147483647;")
a("\t\t\tfiles = (")
for fn in SWIFT:
    a("\t\t\t\t%s /* %s in Sources */," % (bf(fn, "src"), fn))
a("\t\t\t);")
a("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
a("\t\t};")
a("/* End PBXSourcesBuildPhase section */")

common = [
    ("ALWAYS_SEARCH_USER_PATHS", "NO"),
    ("CLANG_ENABLE_MODULES", "YES"),
    ("CLANG_ENABLE_OBJC_ARC", "YES"),
    ("DEAD_CODE_STRIPPING", "YES"),
    ("ENABLE_STRICT_OBJC_MSGSEND", "YES"),
    ("GCC_C_LANGUAGE_STANDARD", "gnu17"),
    ("IPHONEOS_DEPLOYMENT_TARGET", DEPLOY),
    ("SDKROOT", "iphoneos"),
    ("SUPPORTED_PLATFORMS", '"iphoneos iphonesimulator"'),
    ("SWIFT_VERSION", "5.0"),
]
target_common = [
    ("ASSETCATALOG_COMPILER_APPICON_NAME", "AppIcon"),
    ("CODE_SIGNING_ALLOWED", "NO"),
    ("CODE_SIGNING_REQUIRED", "NO"),
    ("CODE_SIGN_IDENTITY", '"-"'),
    ("CODE_SIGN_STYLE", "Manual"),
    ("CURRENT_PROJECT_VERSION", "1"),
    ("DEVELOPMENT_TEAM", '""'),
    ("ENABLE_USER_SCRIPT_SANDBOXING", "NO"),
    ("GENERATE_INFOPLIST_FILE", "NO"),
    ("INFOPLIST_FILE", '%s/Info.plist' % APP_NAME),
    ("IPHONEOS_DEPLOYMENT_TARGET", DEPLOY),
    ("MARKETING_VERSION", "1.0.0"),
    ("PRODUCT_BUNDLE_IDENTIFIER", BUNDLE_ID),
    ("PRODUCT_NAME", '"$(TARGET_NAME)"'),
    ("SUPPORTS_MACCATALYST", "NO"),
    ("SWIFT_VERSION", "5.0"),
    ("TARGETED_DEVICE_FAMILY", "1"),
]


def cfg(cid, name, pairs):
    a("")
    a("\t\t%s /* %s */ = {" % (cid, name))
    a("\t\t\tisa = XCBuildConfiguration;")
    a("\t\t\tbuildSettings = {")
    for k, v in pairs:
        a("\t\t\t\t%s = %s;" % (k, v))
    a("\t\t\t};")
    a("\t\t\tname = %s;" % name)
    a("\t\t};")


a("")
a("/* Begin XCBuildConfiguration section */")
cfg(PROJ_DEBUG_ID, "Debug", common + [
    ("GCC_OPTIMIZATION_LEVEL", "0"),
    ("GCC_PREPROCESSOR_DEFINITIONS", '"DEBUG=1 $(inherited)"'),
    ("SWIFT_OPTIMIZATION_LEVEL", '"-Onone"'),
    ("SWIFT_ACTIVE_COMPILATION_CONDITIONS", "DEBUG"),
])
cfg(PROJ_RELEASE_ID, "Release", common + [
    ("SWIFT_COMPILATION_MODE", "wholemodule"),
    ("SWIFT_OPTIMIZATION_LEVEL", '"-O"'),
    ("VALIDATE_PRODUCT", "YES"),
])
cfg(TARGET_DEBUG_ID, "Debug", target_common + [
    ("SWIFT_ACTIVE_COMPILATION_CONDITIONS", "DEBUG"),
])
cfg(TARGET_RELEASE_ID, "Release", target_common)
a("/* End XCBuildConfiguration section */")

a("")
a("/* Begin XCConfigurationList section */")
for cid, label, dbg, rel in (
    (PROJ_CFG_LIST_ID, 'PBXProject "%s"' % APP_NAME, PROJ_DEBUG_ID, PROJ_RELEASE_ID),
    (TARGET_CFG_LIST_ID, 'PBXNativeTarget "%s"' % APP_NAME, TARGET_DEBUG_ID, TARGET_RELEASE_ID),
):
    a("\t\t%s /* Build configuration list for %s */ = {" % (cid, label))
    a("\t\t\tisa = XCConfigurationList;")
    a("\t\t\tbuildConfigurations = (")
    a("\t\t\t\t%s /* Debug */," % dbg)
    a("\t\t\t\t%s /* Release */," % rel)
    a("\t\t\t);")
    a("\t\t\tdefaultConfigurationIsVisible = 0;")
    a("\t\t\tdefaultConfigurationName = Release;")
    a("\t\t};")
a("/* End XCConfigurationList section */")

a("\t};")
a("\trootObject = %s /* Project object */;" % PROJECT_ID)
a("}")

os.makedirs(PROJ, exist_ok=True)
io.open(os.path.join(PROJ, "project.pbxproj"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")

ws_dir = os.path.join(PROJ, "project.xcworkspace")
os.makedirs(ws_dir, exist_ok=True)
io.open(os.path.join(ws_dir, "contents.xcworkspacedata"), "w", encoding="utf-8", newline="\n").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Workspace version="1.0">\n'
    '   <FileRef location="self:"></FileRef>\n'
    '</Workspace>\n')

scheme_dir = os.path.join(PROJ, "xcshareddata", "xcschemes")
os.makedirs(scheme_dir, exist_ok=True)
bref = ('            <BuildableReference BuildableIdentifier="primary" '
        'BlueprintIdentifier="%s" BuildableName="%s.app" '
        'BlueprintName="%s" ReferencedContainer="container:%s.xcodeproj">\n'
        '            </BuildableReference>' % (TARGET_ID, APP_NAME, APP_NAME, APP_NAME))
scheme = u'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="1500" version="1.7">
   <BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES">
      <BuildActionEntries>
         <BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES">
%s
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES">
      <Testables>
      </Testables>
   </TestAction>
   <LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" debugServiceExtension="internal" allowLocationSimulation="YES">
      <BuildableProductRunnable runnableDebuggingMode="0">
%s
      </BuildableProductRunnable>
   </LaunchAction>
   <ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" savedToolIdentifier="" useCustomWorkingDirectory="NO" debugDocumentVersioning="YES">
      <BuildableProductRunnable runnableDebuggingMode="0">
%s
      </BuildableProductRunnable>
   </ProfileAction>
   <AnalyzeAction buildConfiguration="Debug">
   </AnalyzeAction>
   <ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES">
   </ArchiveAction>
</Scheme>
''' % (bref, bref, bref)
io.open(os.path.join(scheme_dir, APP_NAME + ".xcscheme"), "w", encoding="utf-8", newline="\n").write(scheme)

print("project.pbxproj 生成完成：%d 个 Swift 源文件，资源 Assets.xcassets + www（文件夹引用）" % len(SWIFT))
for fn in SWIFT:
    print("    ", fn)
