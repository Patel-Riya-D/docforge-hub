from IPython.display import Image, display
from backend.statecase.graph import build_graph  # your file

# Build graph
graph = build_graph()

# Display Mermaid PNG
display(Image(graph.get_graph().draw_mermaid_png()))

# Save PNG
graph.get_graph().draw_mermaid_png(
    output_file_path="langgraph.png"
)

print("✅ PNG saved at uploads/diagrams/langgraph.png")