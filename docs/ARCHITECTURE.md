# Wize Wizard Web Architecture

```text
Browser
  │
  ▼
Flask / Waitress
  ├── Authentication + CSRF + RBAC
  ├── Learning Course
  ├── Strategy Process
  ├── Market / Finance / Risk Labs
  └── Admin User Management
          │
          ▼
       SQLite WAL

Static learning assets
  ├── D2 source diagrams
  └── Manim lesson videos
```

The original Textual TUI remains available through `wize-wizard`; the production-oriented web interface uses `wize-wizard-web`.
