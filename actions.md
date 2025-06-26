= SPEC-1: Inventory Management System for Arivu Foods :sectnums: :toc:

== Background Arivu Foods produces a range of flour-based and snack products (e.g., Low-Carb Multi Seeds Atta, Coconut Mixture, Coconut Oil) and distributes them to retail store partners. Each production batch consists of a fixed number of units per product (e.g., 100 units of 1 kg Low-Carb Multi Seeds Atta). Sales agents procure requests from retail partners and dispatch stock accordingly. Remaining units after dispatch are held in centralized inventory. Arivu Foods requires visibility into batch production, inter-store transfers, and month-end stock levels at each partner location and in central inventory.

== Requirements [options="header"] |=== |Priority | Requirement

|Must Have |• Support ~20 retail store partners, with ability to add partners dynamically • Track individual batch numbers, production dates, and expiry dates • Maintain central inventory levels by batch • Record dispatches to each store partner by batch and quantity • Generate monthly stock reports showing remaining units per product and batch at each store and central inventory

|Should Have |• Alert notifications for batches nearing expiry within a configurable threshold • User roles for sales agents and inventory managers with appropriate access controls • Exportable reports (CSV/PDF) for audit and compliance • Dashboard with visual analytics (e.g., stock trends, expiry risk) • Forecasting module to predict reorder requirements based on historical dispatch data

 Dashboard with visual analytics (e.g., stock trends, expiry risk) • Forecasting module to predict reorder requirements based on historical dispatch data

|Won't Have |• Real-time IoT-based store shelf stock monitoring (out of scope for MVP)

|===

== Method

This section describes the system architecture, database schema, and core algorithms for batch-level inventory tracking and dispatch.

=== Architecture Overview The system is a web-based application comprising:

Frontend: HTML5 pages styled with Bootstrap and interactive JavaScript for inventory managers and sales agents.

Backend API: Python-based RESTful service (Flask or Django REST Framework).

Database: PostgreSQL for relational data and batch tracking.

Notifications: Scheduled Python script (cron) for expiry alerts.

==== User Roles and Dashboard Features

Arivu dashboard

: Overview Panel

Total Products: Count of distinct products and active batches.

Aggregate Stock Levels: Bar chart showing units_available per batch, colored by expiry status (green = safe, yellow = nearing expiry, red = expired).

Expiry Dashboard: Table of batches sorted by soonest expiry_date with filter/search, showing batch_id, product_name, expiry_date, units_available.

: Store Monitoring

Partner Map View: Interactive map pinning each store; clicking a pin shows a tooltip with key stock stats (e.g., top 3 low-stock items).

Stock Heatmap: Grid view of stores vs. products, heat intensity representing remaining units.

: Action Widgets

Quick Batch Creation: Button opens modal for new batch entry (pre-populated last used product details).

Dispatch Shortcut: In-dashboard mini-form to select store and batch for fast dispatch without navigating away.

: Reporting & Alerts

Monthly Report Generator: Date picker + “Generate” button; on click, renders downloadable PDF/CSV links and preview table.

Alert Center: Sidebar panel listing critical alerts (expired batches, low stock thresholds breached) with acknowledgment controls.

Store Partner dashboard

: Store Snapshot

Current Inventory List: Paginated list of batch_id, product_name, expiry_date, units_on_hand, with in-line search and sort.

Low-Stock Indicators: Inline badges for items below reorder threshold, with “Reorder” button next to each.

: Reorder Workflow

Bulk Request Form: Checkbox selection of multiple batches, input desired quantities, and submit single request.

Request Status Tracker: Table listing past requests with request_date, batch_id, quantity_requested, status (Pending, Approved, Dispatched).

: Dispatch History

Recent Dispatches: Chronological feed of last 10 dispatch events with date, product, quantity, and dispatcher notes.

Download Statement: Button to export store-specific dispatch history for the selected date range.

: Notifications & Settings

Alert Preferences: Toggle to set reorder threshold per product and choose notification channel (email/in-app).

Profile & Store Info: View and edit store contact details, address, and assignment of new users.

=== Batch Management [plantuml, wire-batch, png]

@startuml wireframe { title "Batch Management" form { label "Product" dropdown ["Low-Carb Atta", "Coconut Flour", ...] label "Production Date" input date label "Expiry Date" input date label "Total Units" input number button "Create Batch" } list { | Batch ID | Product | Expiry | Units | Actions | | Batch001 | Atta | 2025-12-01 | 100 | [Edit] [Delete] | } } @enduml

=== Dispatch Form [plantuml, wire-dispatch, png]

@startuml wireframe { title "Dispatch Stock" form { label "Select Store" dropdown ["Store A", "Store B", ...] label "Select Batch" dropdown ["Batch001", "Batch002", ...] label "Quantity" input number button "Dispatch" } } @enduml

=== Monthly Reports [plantuml, wire-reports, png]

@startuml wireframe { title "Monthly Reports" header { "Select Month: [2025-06]" button "Generate" } table { | Product | Batch | Central | Store A | Store B | ... | | Atta | Batch001 | 45 | 20 | 35 | } button "Export CSV" button "Export PDF" } @enduml


== Gathering Results

Validate that all REST endpoints return correct data; perform end-to-end API testing.

Verify batch allocation reduces central inventory and updates store inventory correctly.

Confirm monthly reports match actual stock levels in database.

Ensure expiry alerts are triggered for batches within threshold and delivered via email/in-app.

Collect user feedback from sales agents on mobile UI usability and iterate as needed.

