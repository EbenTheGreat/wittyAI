#  WittyAI

A fun interactive **LangGraph-powered Joke Bot** that generates, critiques, and saves developer-themed jokes with embeddings stored in **Pinecone**.  
It supports multiple joke categories, languages, and persistence so you can browse previously saved jokes.


---

##  Features
- Generate short, developer-themed jokes (Dad Developer, Chuck Norris Developer, or General).
- Human-in-the-loop approval: approve or reject jokes before saving.
- Multilingual joke generation (supports `cs, de, en, es, eu, fr, gl, hu, it, lt, pl, ru, sv`).
- Joke embeddings created using **VoyageAI** (`voyage-3.5`).
- Persistent joke storage using:
  - **Pinecone** (vector search for duplicate detection).
  - **JSON catalog** (local browsing).
- Interactive CLI menu:
  - [n] Generate new joke  
  - [c] Change category  
  - [l] Change language  
  - [r] Reset joke history  
  - [b] Browse saved jokes  
  - [q] Quit  


---

##  Project Structure
```
│── bot/
│── config/ # Config files for prompts & settings
│── .env # Environment variables
│── errors.md # Debugging logs
│── graph.mmd # Graph visualization (Mermaid)
│── jokes_catalog.json # Saved jokes catalog
│── llm.py # LLM setup (Groq API)
│── main.py # Entry point (build & run graph)
│── paths.py # File path helpers
│── persistence.py # Pinecone + JSON persistence
│── requirements.txt # Python dependencies
│── utils.py # Config utilities
```

---

##  JokeState
```python
class JokeState(BaseModel):
    jokes: Annotated[List[Joke], add] = []
    jokes_choice: Literal["n", "c", "l", "r", "q"] = "n"
    joke_embeddings: List[List[float]] = []
    category: str = "general"
    language: str = "en"
    latest_jokes: str = ""
    approved_status: bool = False
    retry_count: int = 0
    quit: bool = False
```


##  Setup

### 1. Clone repository
```bash
git clone https://github.com/EbenTheGreat/wittyAI.git
   ```

### 2. Set environment variables:
   ```bash
   export PINECONE_API_KEY="your-key"
   export VOYAGE_API_KEY="your-key"
   ```

### 3. Install dependencies
   ```bash
   pip install -r requirements.txt

   ```

### 4. Environment Variables
   ```
Create a .env file in the project root:

   VOYAGE_API_KEY=your_voyage_api_key
   GROQ_API_KEY=your_groq_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=jokes-index
   PINECONE_ENVIRONMENT=us-east-1
   ```

### 5. Run the Joke Bot
```python
python main.py
```

## Graph Visualization

The joke bot workflow is built with LangGraph. You can export the graph as a Mermaid diagram:
```python
graph = build_joke_graph()
with open("graph.mmd", "w") as f:
    f.write(graph.get_graph().draw_mermaid())
  ```

Then preview the diagram with Mermaid Live Editor
.

## Joke Catalog

Approved jokes are saved in: Pinecone: for embeddings + duplicate detection.

jokes_catalog.json: for local browsing.

Example entry:
   ```json
   {
     "id": "8c7fb7b4-814c-4e56-aa9f-17a04310545b",
     "text": "Why do developers name their functions with unnecessary abbreviations? Because they're trying to branch out but end up forking their own sanity.",
     "category": "general",
     "timestamp": "2025-10-04T13:33:52.076282"
   }
   ```

## Next Steps / Improvements

- Add automated LLM critic alongside human critic.

- Build a web frontend with Streamlit or FastAPI.

- Add more categories (AI, DevOps, Security).

- Implement joke search powered by Pinecone.




