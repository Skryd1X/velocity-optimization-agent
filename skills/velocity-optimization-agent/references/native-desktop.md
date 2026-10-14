# Native and desktop adapters

Android: use a representative release/profile build and platform tools for startup, frame timing, ANR/hangs, memory and lifecycle. Consider Baseline/Startup Profiles, R8 and initialization changes only when compatible with the real app and verified by measurements. Debug timing does not establish release performance. Check startup from notifications/deep links as well as the launcher.

iOS/macOS: use available Xcode/Instruments/XCTest/MetricKit evidence for responsiveness, hangs, allocations/leaks, I/O, network and power. Simulator results do not prove actual phone GPU, energy or thermal behavior. Preserve main-thread UI correctness when moving work asynchronously. Document required macOS/device access when unavailable on this host.

Flutter: profile in the appropriate mode, inspect widget rebuilds, layout/raster work, lists, expensive rendering effects and asset/decode costs using current framework guidance. React Native: inspect JS and native/UI-thread work, bridge/state patterns, lists, images and navigation using the supported runtime. Neither inherits browser field metrics as its native acceptance criteria.

Desktop shells/native clients: measure launch, memory growth, IPC, renderer work, I/O, background activity and window resizing/OS scaling. Inspect Electron/Tauri/native code paths actually present. Keep keyboard behavior, titlebar/safe regions and multi-display movement functional. Native UI needs platform automation and actual captures.

A platform adapter consists of discovery signals, evidence tools, meaningful journeys, metrics, repairs and acceptance—not just a directory of device sizes. Missing host tools are explicit blockers for the corresponding runtime layer.
