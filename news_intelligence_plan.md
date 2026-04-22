# Real-Time News Intelligence Pipeline

## Overview

This project is a home-lab friendly system for collecting near-real-time social and news signals, processing them with NLP, storing relationships in a graph database, and visualizing emerging topics as an intelligence dashboard.

The initial deployment target is a single-node Ubuntu home server running on an old gaming laptop. The design keeps the first version simple while leaving room for future scaling into a distributed setup.

---

## Goals

- Collect trending and breaking-topic signals from public web sources
- Extract keywords, entities, and topic relationships using NLP
- Store relationships in a graph database for exploration and analysis
- Provide a visual dashboard for near-real-time updates
- Keep the system lightweight enough to run on a home lab server
- Design the stack so it can later evolve into a multi-node distributed system

---

## Core Use Case

The system should be able to:

1. Fetch fresh content from sources such as RSS feeds, Google News, Reddit, and Twitter-like public endpoints
2. Clean and normalize incoming text
3. Extract:
   - keywords
   - named entities
   - topic clusters
   - optional sentiment
4. Store:
   - raw documents in relational storage
   - relationships in a graph database
5. Display:
   - trending topics
   - connected entities
   - evolving clusters over time
   - alerts for sudden spikes

---

## Phase 1: MVP Architecture

### High-Level Flow

```text
Sources → Fetcher → NLP Pipeline → Storage → Graph DB → Dashboard
```

### Recommended MVP Sources

- Google News RSS
- Reddit RSS
- Public RSS feeds from technology, finance, security, or world news sites
- Optional Twitter/Nitter-like feeds where legally and technically practical

### MVP Components

#### 1. Ingestion Layer
Purpose:
- fetch fresh data every 1 to 5 minutes
- deduplicate content
- normalize timestamps and source metadata

Suggested tools:
- Python
- `feedparser`
- `requests`
- `beautifulsoup4` for fallback scraping
- cron for scheduling

#### 2. Processing Layer
Purpose:
- clean raw text
- extract keywords
- extract named entities
- generate topic clusters
- optionally score sentiment

Suggested tools:
- `spaCy`
- `KeyBERT`
- `sentence-transformers`
- `scikit-learn`

#### 3. Storage Layer
Purpose:
- keep raw and processed data available for reprocessing and auditing

Suggested storage split:
- PostgreSQL or SQLite for raw items and metadata
- Neo4j for graph relationships

#### 4. Graph Layer
Purpose:
- represent links between topics, people, companies, places, and source items

Example node types:
- `Article`
- `Tweet`
- `Topic`
- `Person`
- `Organization`
- `Location`
- `Source`

Example relationships:
- `MENTIONS`
- `RELATED_TO`
- `PUBLISHED_BY`
- `TRENDING_ON`
- `CO_OCCURS_WITH`

#### 5. Visualization Layer
Purpose:
- explore topic clusters and entity relationships visually

Suggested tools:
- Neo4j Bloom
- Grafana
- optional custom web UI with D3.js later

---

## Concrete Single-Node Deployment

### Host Machine

Target hardware:
- old gaming laptop
- headless Ubuntu Server
- connected to home router over Ethernet if possible

Expected sufficient specs:
- quad-core or better CPU
- 16 GB RAM preferred
- SSD preferred

### Suggested Deployment Model

Use Docker Compose to run the whole stack on one machine.

Services:
- `ingestion-worker`
- `nlp-worker`
- `postgres`
- `neo4j`
- `grafana`
- optional `redis` later

### Why Docker Compose

- simple service isolation
- easy startup and restart
- easy backups
- easier migration to a new host later
- good stepping stone toward Kubernetes or distributed deployment

---

## Recommended Directory Structure

```text
news-intel/
├── docker-compose.yml
├── .env
├── README.md
├── ingestion/
│   ├── fetch_rss.py
│   ├── fetch_reddit.py
│   ├── deduplicate.py
│   └── sources.yaml
├── processing/
│   ├── clean_text.py
│   ├── extract_entities.py
│   ├── extract_keywords.py
│   ├── cluster_topics.py
│   └── sentiment.py
├── storage/
│   ├── postgres_schema.sql
│   └── neo4j_loader.py
├── dashboard/
│   ├── grafana/
│   └── queries/
├── scheduler/
│   └── cron_jobs.txt
└── docs/
    └── architecture.md
```

---

## Data Model

### Relational Storage

Store the raw content in PostgreSQL or SQLite with fields like:

- `id`
- `source_name`
- `source_type`
- `title`
- `url`
- `published_at`
- `fetched_at`
- `raw_text`
- `clean_text`
- `language`
- `hash`

Purpose:
- audit trail
- deduplication
- reprocessing when NLP improves
- timeline queries

### Graph Storage

Store extracted entities and relationships in Neo4j.

Example structure:

```text
(Article)-[:MENTIONS]->(Organization)
(Article)-[:MENTIONS]->(Person)
(Article)-[:HAS_TOPIC]->(Topic)
(Topic)-[:RELATED_TO]->(Topic)
(Organization)-[:CO_OCCURS_WITH]->(Organization)
(Topic)-[:TRENDING_ON]->(Day)
```

This enables:
- graph exploration
- emerging cluster detection
- influence mapping
- topic evolution analysis

---

## Processing Pipeline

### Step 1: Fetch
Pull recent entries from configured feeds.

### Step 2: Clean
Remove HTML, normalize whitespace, strip tracking parameters, and standardize encoding.

### Step 3: Deduplicate
Use URL normalization and content hashing.

### Step 4: NLP Enrichment
Run:
- named entity recognition
- keyword extraction
- topic clustering
- optional sentiment scoring

### Step 5: Persist
- save raw and cleaned documents to relational storage
- update entities and relationships in Neo4j

### Step 6: Visualize
Expose results to dashboard and graph explorer.

---

## Scheduling Strategy

### Initial Choice
Use cron jobs.

Example cadence:
- fetch every 2 minutes
- process immediately after fetch
- refresh dashboard every minute or on query

Reason:
- very simple
- low overhead
- good enough for MVP

### Future Upgrade
Move to:
- Redis + Celery
or
- Kafka + stream workers

Use this only after the MVP is stable.

---

## Dashboard Features

### MVP Dashboard

Should show:
- top keywords in the last hour
- top entities in the last hour
- most connected topics
- source activity over time
- graph exploration panel

### Future Dashboard Features

- entity drill-down view
- topic timeline playback
- geographic mapping
- per-category dashboards
- alert panels for spike detection

---

## Near-Real-Time Alerting

A simple first approach:

- calculate keyword frequency over rolling windows
- compare current frequency to previous baseline
- trigger an alert when there is a sharp increase

Alert outputs:
- log entry
- Telegram bot message
- email
- on-screen dashboard alert

Example:
- sudden surge in mentions of a company, country, vulnerability, or public event

---

## Security and Operations

### Home Lab Safety

- expose only the dashboard or web UI if needed
- do not expose databases directly to the internet
- use strong passwords and secrets in `.env`
- keep Ubuntu patched
- use firewall rules
- prefer VPN access to the home network instead of direct port forwarding

### Backups

Back up:
- Neo4j data
- PostgreSQL database
- configuration files
- source lists
- dashboard configuration

Backup targets:
- external drive
- NAS
- encrypted cloud backup if available

---

## Resource Expectations

A single-node MVP should fit comfortably on a machine with 16 GB RAM.

Rough estimate:
- Neo4j: 1 to 2 GB
- PostgreSQL: 0.5 to 1 GB
- NLP workers: 1 to 3 GB depending on models
- Grafana: low
- OS and overhead: remaining balance

This keeps the MVP practical for a home-lab server.

---

## Phased Build Plan

## Phase 1: Basic Ingestion
Deliverables:
- RSS fetching
- raw storage
- deduplication

Success criteria:
- can reliably collect and store fresh items

## Phase 2: NLP Enrichment
Deliverables:
- keyword extraction
- entity extraction
- basic clustering

Success criteria:
- extracted entities and keywords are usable and meaningful

## Phase 3: Graph Construction
Deliverables:
- Neo4j schema
- graph loader
- relationship generation

Success criteria:
- graph queries reveal useful topic connections

## Phase 4: Visualization
Deliverables:
- Neo4j Bloom setup
- simple Grafana dashboards

Success criteria:
- can visually inspect trends and relationships

## Phase 5: Alerting
Deliverables:
- spike detection
- notification channel

Success criteria:
- system highlights unusual activity without too many false positives

## Phase 6: Scaling and Distribution
Deliverables:
- separate ingestion and processing services
- optional multi-node deployment

Success criteria:
- system handles more feeds and more frequent updates reliably

---

## Future Distributed Architecture

Once the MVP works, the system can be split across multiple nodes.

Example:
- Node 1: ingestion
- Node 2: NLP processing
- Node 3: graph database and dashboard

Possible future technologies:
- Kafka
- Redis
- Celery
- Kubernetes
- MinIO for object storage

This future version aligns well with research interests in:
- distributed systems
- streaming data pipelines
- graph analytics
- real-time intelligence systems

---

## Suggested Initial Tech Stack

### Core
- Python
- Docker Compose
- Ubuntu Server

### Data Ingestion
- `feedparser`
- `requests`
- `beautifulsoup4`

### NLP
- `spaCy`
- `KeyBERT`
- `sentence-transformers`
- `scikit-learn`

### Storage
- PostgreSQL or SQLite
- Neo4j

### Visualization
- Neo4j Bloom
- Grafana

### Scheduling
- cron initially
- Redis/Celery later if needed

---

## First Build Milestone

The first practical milestone should be:

> Collect RSS news every 2 minutes, store the raw text in PostgreSQL, extract entities with spaCy, and write entity-topic relationships into Neo4j for visualization.

That milestone is large enough to prove the concept but still manageable on a home lab server.

---

## Next Actions

1. Create the repository structure
2. Write `docker-compose.yml`
3. Set up PostgreSQL and Neo4j
4. Build the RSS ingestion script
5. Add entity extraction with spaCy
6. Write the Neo4j loader
7. Create a small visualization workflow
8. Add alerting after the pipeline is stable

---

## Stretch Goals

- sentiment and stance tracking
- multilingual support
- topic summarization with local LLMs
- event deduplication across sources
- financial and cybersecurity specific dashboards
- ARM cluster deployment for experimentation
- benchmark single-node versus distributed performance

---

## Summary

This project is feasible on a single Ubuntu home server and can begin as a lightweight but powerful MVP. The best path is to start with RSS ingestion, NLP enrichment, Neo4j graphing, and simple dashboards. Once stable, the architecture can expand into a distributed real-time intelligence platform.
