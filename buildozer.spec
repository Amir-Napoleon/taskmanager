[app]
title = Task Manager
package.name = mytaskmanager
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,csv,txt
version = 1.0
requirements = python3,kivy==2.3.0,jdatetime,arabic-reshaper,python-bidi,plyer
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, POST_NOTIFICATIONS
android.api = 33
android.minapi = 24
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1