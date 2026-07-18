# Resume Bullet Points – AI Pulse

## Short Project Description
**AI Pulse: GenAI Industry Trends Warehouse**  
Engineered an end-to-end data pipeline and analytics platform that ingests, scores, and visualizes generative AI industry news from multiple external APIs using a medallion-inspired architecture.

## Resume Points
• **Designed and implemented** a multi-source ETL pipeline using Python to ingest AI industry news data from GNews and Hacker News APIs, standardizing disparate JSON structures into a unified schema.
• **Optimized data ingestion performance** by utilizing Python's `ThreadPoolExecutor` for concurrent API requests, significantly reducing overall data fetching time.
• **Architected a medallion-inspired PostgreSQL data warehouse**, implementing logical separation between raw ingestion data and a validated staging layer to ensure data integrity and query reliability.
• **Developed a custom AI Intelligence Scoring algorithm** (0-100) using Pandas, evaluating articles based on keyword density, source credibility, and temporal relevance to rank industry news.
• **Built a 7-page interactive analytics dashboard** using Streamlit and Plotly, featuring complex filtering, pagination, and data visualizations (histograms, trend lines, donut charts) for analytics and decision-support insights.
• **Implemented robust error handling and data validation** within the ETL process, utilizing SQLAlchemy for connection pooling and ensuring bad data is rejected before entering the staging environment.
• **Containerized the entire application stack** (Python pipeline, Streamlit frontend, and PostgreSQL database) using Docker and Docker Compose, ensuring consistent deployment across different environments.
• **Established a comprehensive testing suite** with over 30 unit tests, verifying data transformation logic, API integration edge cases, and the accuracy of the intelligence scoring system.
• **Applied advanced Streamlit state management** (session state flags) to resolve complex UI synchronization issues and prevent widget instantiation errors during dashboard filtering and resets.

## Skills Demonstrated
- **Data Engineering:** ETL Pipelines, Data Validation, Medallion Architecture
- **Databases:** PostgreSQL, SQLAlchemy, Schema Design
- **Programming:** Python, Pandas, Concurrent Execution (Threading)
- **Web/UI:** Streamlit, Plotly, Dashboard Development, UX/UI Polish
- **DevOps/Tools:** Docker, Docker Compose, Git, API Integration
- **Testing:** Unit Testing, Pytest, Error Boundary Implementation
