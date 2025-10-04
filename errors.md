# Errors and Lessons Learned - LangGraph Joke Bot Project

This document records the errors encountered during development of the Joke Bot project using LangGraph, along with the lessons learned from each issue.

---

## 1. Module Import Errors
**Error:**
```bash
ModuleNotFoundError: No module named 'frontend'
```
**Cause:** Attempted to import a non-existent or misplaced module.  
**Lesson Learned:** Always verify the project structure and ensure imports match the actual folder/file organization.

---

## 2. FileNotFoundError for prompt_config.yaml
**Error:**
```bash
FileNotFoundError: [Errno 2] No such file or directory: '.../config/prompt_config.yaml'
```
**Cause:** The program looked for `prompt_config.yaml` in the wrong directory.  
**Lesson Learned:** Keep configuration files in a clearly defined path and verify relative vs. absolute paths. Use `os.path.join` to avoid mistakes.

---

## 3. API Connection Issues
**Error:**
```bash
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='research-assistant-oe9n.onrender.com', ...)
```
**Cause:** The host could not be resolved or internet connection was unstable.  
**Lesson Learned:** Confirm that APIs are deployed and reachable. Use `ping` or `curl` to verify connectivity before debugging code.

---

## 4. Misconfigured Prompt (Wrong Field Injection)
**Issue:** Jokes did not use the selected language or category.  
**Cause:** Prompt construction used placeholders incorrectly, e.g.:
```python
prompt += f"\n\nThe category is: {state.language}"
prompt += f"\n\nThe category is: {state.category}"
```
This caused confusion in output.  
**Lesson Learned:** Be precise in prompt building, and ensure variables like `language` and `category` are injected in the right context.

---

## 5. Writer–Critic Loop Not Triggering Properly
**Issue:** The writer-critic loop didn’t always repeat.  
**Cause:** Router logic was incomplete:
```python
if state.approved or state.retry_count >= 5:
    return "show_final_joke"
return "writer"
```
**Lesson Learned:** Carefully define routing edges to enforce desired behavior. Test each condition with multiple inputs.

---

## 6. Misunderstanding Between Language vs Category
**Issue:** Language selection worked, but the joke generator treated language as category.  
**Lesson Learned:** Clearly separate and name state fields (e.g., `state.language`, `state.category`) to avoid overlap.

---

## 7. Pinecone Integration Slowness
**Issue:** Program took very long to start or save jokes.  
**Cause:** Pinecone client and index were being reinitialized multiple times instead of once.  
**Lesson Learned:** Initialize Pinecone client and index once globally, and reuse them across nodes to reduce overhead.

---

## 8. AttributeError: Pinecone client
**Error:**
```bash
AttributeError: 'Pinecone' object has no attribute 'index'. Did you mean: 'Index'?
```
**Cause:** Used the wrong method (`pc.index`) instead of `pc.Index`.  
**Lesson Learned:** Double-check Pinecone SDK methods—current versions require `pc.Index("name")`.

---

## 9. KeyError: 'browse_jokes'
**Error:**
```bash
KeyError: 'browse_jokes'
During task with name 'show_menu'
```
**Cause:** A menu option (`b`) mapped to `browse_jokes`, but the node was not registered in the graph’s routing.  
**Lesson Learned:** Always ensure new menu actions are added both as nodes and edges in the graph definition.

---

## 10. Graph Visualization Not Showing
**Issue:** Wanted to see the graph, but nothing was rendered.  
**Cause:** Did not generate or open the `graph.mmd` file.  
**Lesson Learned:** Use `graph.get_graph().draw_mermaid()` to export to `.mmd`, and view with [mermaid.live](https://mermaid.live) or VS Code’s Mermaid preview extension.

---

## General Lessons
- Always keep configs in sync with your codebase.  
- Add logging (`print` or proper logger) to inspect the state at each node.  
- Test small components (like router logic) independently before wiring the full graph.  
- Be explicit in prompt engineering: the LLM outputs only what you ask it to.  
- Optimize for performance: reuse Pinecone client and embedding models instead of creating them repeatedly.  
- When extending functionality (like adding `browse_jokes`), update both the state machine **and** the graph connections.  

---

With each error fixed, the system became more robust and predictable!
