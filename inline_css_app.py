import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="Inline CSS for Canvas", layout="centered")

st.title("HTML + CSS → Canvas-safe HTML")
st.markdown(
    """
This tool embeds external CSS files directly into an HTML file
so it will display correctly when uploaded to Canvas.  App written by ChatGPT.
"""
)

html_file = st.file_uploader(
    "Upload HTML file",
    type=["html", "htm"]
)

css_files = st.file_uploader(
    "Upload CSS file(s)",
    type=["css"],
    accept_multiple_files=True
)

def inline_css(html_text, css_texts):
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove external stylesheet links
    for link in soup.find_all("link", rel="stylesheet"):
        link.decompose()

    # Ensure <head> exists
    if soup.head is None:
        head = soup.new_tag("head")
        soup.html.insert(0, head)
    else:
        head = soup.head

    # Create <style> tag
    style = soup.new_tag("style")
    style.string = "\n\n".join(css_texts)

    head.append(style)

    return str(soup)

def make_inline_filename(original_name, suffix="_inline"):
    if "." in original_name:
        base, ext = original_name.rsplit(".", 1)
        return f"{base}{suffix}.{ext}"
    else:
        return f"{original_name}{suffix}.html"

if html_file and css_files:
    output_name = make_inline_filename(html_file.name)

    if st.button("Create Canvas-safe HTML"):
        html_text = html_file.read().decode("utf-8")
        css_texts = [f.read().decode("utf-8") for f in css_files]

        output_html = inline_css(html_text, css_texts)

        st.success("Done! Your HTML is now self-contained.")

        st.download_button(
            label="Download standalone HTML",
            data=output_html,
            file_name=output_name,
            mime="text/html"
        )
