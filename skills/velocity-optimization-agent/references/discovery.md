# Project discovery

Treat file patterns as signals, not conclusions. package.json can describe a web app, Electron shell, React Native client, utility or monorepo. Inspect dependencies, entry points, build settings and actual execution before labeling a component. Telegram SDK references, WebView wrappers, Android manifests, Xcode projects, Flutter pubspec, native entry points and backend manifests help route the task.

Discover multiple components and shared dependencies. Map routes/screens to services, database/cache access and background consumers. Record public/admin/user-specific journeys and data ownership boundaries. Read project instructions and preserve unrelated changes. Inspect untrusted project scripts before executing them.

Record startup/build/test commands, environment assumptions, ports, supported platforms, unavailable credentials and baseline failures. Never print .env contents just to inventory their existence. The helper skips common generated/dependency directories and reads bounded manifests, so unvisited/excluded paths stay documented.

For each detected component define evidence needs: source, local executable, staging, deployed, emulator/simulator or physical device. If a native app cannot run on this host, finish meaningful source work and explicitly retain runtime validation as blocked. Do not rebuild an existing project into a preferred framework to make testing easier.
