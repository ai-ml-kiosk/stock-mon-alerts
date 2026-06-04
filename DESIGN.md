# Application Software Design Document (DESIGN.md)

## 1. System Overview
The **Smart Stock Monitor Agent** is a reactive financial dashboard built on Streamlit. The application allows users to search global equity tickers via an intelligent typeahead interface, visualizes historical pricing trends, and intercepts incoming news feeds to inject single-sentence, cloud-accelerated LLM analytical summaries whenever native publisher summaries are missing.

---

## 2. File Architecture & Dependencies

```mermaid
graph TD
    %% UI Layer
    A[app.py Streamlit UI] --> B[streamlit_searchbox Typeahead]
    
    %% Service Layer
    A --> C[services/data_fetcher.py]
    A --> D[services/article_filter.py]
    
    %% Shared Contracts
    A --> E[src/schemas.py StockArticle]
    C --> E
    D --> E
    
    %% External API Targets
    B --> F[Yahoo Finance Autocomplete API]
    C --> G[yfinance Library Engine]
    C --> H[Groq API Endpoint]