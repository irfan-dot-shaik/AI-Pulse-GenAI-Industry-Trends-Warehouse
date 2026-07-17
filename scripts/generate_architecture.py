import os
from playwright.sync_api import sync_playwright

html_content = """
<!DOCTYPE html>
<html>
<head>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true, theme: 'dark' });
  </script>
  <style>
    body { background-color: #0E1117; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .mermaid { font-family: sans-serif; }
  </style>
</head>
<body>
  <div class="mermaid">
    graph TD;
        G[GNews] --> I[Ingestion Layer]
        H[HackerNews] --> I
        R[Reddit] --> I
        I --> V[Validation]
        V --> T[Transformation]
        T --> S[AI Scoring]
        S --> P[PostgreSQL Warehouse]
        P --> A[Analytics Layer]
        A --> UI[Streamlit Dashboard]
        
        style G fill:#2C3E50,stroke:#F7F5F2,color:#F7F5F2
        style H fill:#2C3E50,stroke:#F7F5F2,color:#F7F5F2
        style R fill:#2C3E50,stroke:#F7F5F2,color:#F7F5F2
        style I fill:#27AE60,stroke:#F7F5F2,color:#F7F5F2
        style V fill:#2980B9,stroke:#F7F5F2,color:#F7F5F2
        style T fill:#2980B9,stroke:#F7F5F2,color:#F7F5F2
        style S fill:#8E44AD,stroke:#F7F5F2,color:#F7F5F2
        style P fill:#F39C12,stroke:#F7F5F2,color:#F7F5F2
        style A fill:#D35400,stroke:#F7F5F2,color:#F7F5F2
        style UI fill:#C0392B,stroke:#F7F5F2,color:#F7F5F2
  </div>
</body>
</html>
"""

def generate_architecture_diagram():
    with open("temp_mermaid.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 800, "height": 800})
        
        page.goto(f"file://{os.path.abspath('temp_mermaid.html')}", wait_until="networkidle")
        page.wait_for_timeout(2000) # Wait for mermaid to render
        
        # Get bounding box of the mermaid element
        element = page.locator(".mermaid")
        box = element.bounding_box()
        
        os.makedirs("docs/images", exist_ok=True)
        
        # Screenshot just the diagram with some padding
        page.screenshot(
            path="docs/images/architecture.png",
            clip={
                "x": max(0, box["x"] - 20),
                "y": max(0, box["y"] - 20),
                "width": box["width"] + 40,
                "height": box["height"] + 40
            }
        )
        browser.close()
        
    os.remove("temp_mermaid.html")
    print("Architecture diagram generated at docs/images/architecture.png")

if __name__ == "__main__":
    generate_architecture_diagram()
