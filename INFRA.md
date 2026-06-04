# System Infrastructure & Tooling Matrix (INFRA.md)

## 1. Host Hardware Specifications
All local engineering services, IDE frameworks, and running development servers are physically hosted on the following bare-metal equipment setup:

* **Compute Node:** Dell Latitude 7480 Enterprise Laptop
* **Memory Configuration:** 16GB DDR4 RAM (Provides the stable headroom necessary to concurrently host a multi-threaded Streamlit server, active terminal daemons, background text editors, and containerized local AI models without swapping).
* **Execution Runtime Environment:** Python 3.12 managed within isolated Virtual Environments (`venv`) to keep package namespaces clean.

---

## 2. Infrastructure Architecture Map

```mermaid
graph LR
    subgraph Local Host Environment [Dell Latitude 7480 - 16GB RAM]
        A[VS Code Workspace]
        B[Cline Extension]
        C[Aider CLI Git-Aided Terminal]
        D[Ollama Local Engine]
    end

    subgraph Cloud Inference Tier [External API Integrations]
        E[Groq Cloud API LPU Cluster]
        F[OpenRouter Free Tier Gateway]
    end

    A <--> B
    C --> A
    B -.->|Local Sandbox Testing| D
    A ==>|Production Traffic| E
    B -.->|Alternate Model Benchmarking| F