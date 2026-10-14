# Web, PWA and mini-app adapters

Analyze the critical rendering path, route bundles, dependency duplication, unnecessary JS, code splitting, third-party scripts, image/font delivery and server rendering/hydration. Prioritize required content; avoid lazy-loading the important initial image without a reason. Reserve media space and preserve image quality at actual display sizes. Measure before adding memoization, virtualization or another library.

Follow framework-specific profiling for re-renders, state subscriptions, expensive calculations, list keys, DOM volume, event handling, request duplication, cleanup and memory growth. Check ordinary navigation and return visits, not just first page load. Browser throttling approximates conditions and does not recreate every low-end phone or network.

PWA/service workers: version assets, verify update/recovery and offline behavior, avoid stale identity/private data, and test old/new clients during rollout. Cancellation/retry must preserve data correctness. Caches that cross identity boundaries need Aegis review.

Telegram Mini Apps: verify host initialization, API availability/fallback, dynamic versus stable viewport height, safeAreaInset/contentSafeAreaInset, expansion/fullscreen, theme changes, back/main buttons, keyboard and resume/minimize behavior. A standalone browser cannot establish Telegram host behavior. Inspect actual client environments for host-specific acceptance.

Embedded WebView: inspect supported engine, host bridge/lifecycle, navigation, keyboard, scroll and storage behavior. Native wrapper startup and memory need native profiling. Do not treat user-agent spoofing as a complete WebView/native-device test.

Motion/WebGL: measure main-thread work, layout/paint, layer cost, render loops, textures/geometry, DPR, offscreen/background work and cleanup. Preserve meaningful art direction and choose intentional lower-cost tiers. Route complex visual or motion changes to Kinesis rather than replacing the identity casually.
