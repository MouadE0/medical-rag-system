# Application Screenshots

Visual walkthrough of the Medical RAG system.

---

## 1. Login Screen

![Login](screenshots/1-login.png)

Simple authentication with username/password. Default credentials (for local DEV only):
- Admin: `admin` / `admin123`
- Doctor: `doctor` / `doctor123`

---

## 2. Main Dashboard

![Dashboard](screenshots/2-dashboard.png)

Interface with:
- Query input field
- Number of suggestions selector (To be improved)
- Re-ranking toggle
- Submit button
- ...

---

## 3. Query Input Example

![Query Input](screenshots/3-query-input.png)

Example query: "Dyspnée à l'effort avec toux"

Each suggestion shows:
- CIM-10 code (e.g., R06.0)
- Label/description
- Relevance score (0-1)
- Clinical explanation
- Exclusions and Inclusions (If any)
- CoCoA rules section


Results ordered by relevance.
---


## 4. Code Lookup

![Multiple Results](screenshots/4-CodeLookup.png)

Possibility to look up a specific code through the app.

---
## 5. History of the queries

![Multiple Results](screenshots/5-History.png)



[← Back to main README](../README.md)