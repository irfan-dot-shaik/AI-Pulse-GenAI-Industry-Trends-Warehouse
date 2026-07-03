from streamlit.testing.v1 import AppTest
import json

at = AppTest.from_file("dashboard/pages/03_Top_AI_News.py")
at.run()

for i, md in enumerate(at.markdown):
    if "</div>" in md.value:
        print(f"--- Block {i} (len {len(md.value)}) ---")
        print(md.value)

for i, err in enumerate(at.exception):
    print(err)
