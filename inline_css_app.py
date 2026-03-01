import re
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="Inline CSS for Canvas", layout="centered")

st.title("HTML + CSS → Canvas-safe HTML")
st.markdown(
    """
This tool embeds external CSS files directly into an HTML file
so it will display correctly when uploaded to Canvas. App written by ChatGPT.
"""
)

html_file = st.file_uploader("Upload HTML file", type=["html", "htm"])

css_files = st.file_uploader(
    "Upload CSS file(s)", type=["css"], accept_multiple_files=True
)

# -----------------------------
# Helpers
# -----------------------------
def inline_css(html_text: str, css_texts: list[str]) -> str:
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove external stylesheet links
    for link in soup.find_all("link", rel="stylesheet"):
        link.decompose()

    # Ensure <head> exists
    if soup.head is None:
        # If there's no <html> wrapper, create one (rare but can happen)
        if soup.html is None:
            html_tag = soup.new_tag("html")
            # Move all existing nodes into <html>
            for node in list(soup.contents):
                html_tag.append(node.extract())
            soup.append(html_tag)

        head = soup.new_tag("head")
        soup.html.insert(0, head)
    else:
        head = soup.head

    # Create <style> tag (append at end so it wins)
    style = soup.new_tag("style")
    style.string = "\n\n".join(css_texts)
    head.append(style)

    return str(soup)


def make_inline_filename(original_name: str, suffix: str = "_inline") -> str:
    if "." in original_name:
        base, ext = original_name.rsplit(".", 1)
        return f"{base}{suffix}.{ext}"
    return f"{original_name}{suffix}.html"


def fix_latexml_numbering_for_canvas(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Canvas often strips/ignores <head><style> when pasting into a Page.
    LaTeXML numbering frequently uses:
      <ol class="ltx_enumerate"> with <li style="list-style-type:none;">
      plus a separate <span class="ltx_tag ltx_tag_item">1.</span>
    Without CSS, the span stays on its own line.

    Fix: convert to native <ol>/<li> numbering by:
      - removing list-style-type:none
      - removing the ltx_tag span that contains the number label
    """
    # Only target LaTeXML-style enumerations
    for ol in soup.select("ol.ltx_enumerate"):
        for li in ol.select("li.ltx_item"):
            # 1) Remove list-style-type:none if present (inline style)
            if li.has_attr("style"):
                # drop only list-style-type declarations; keep other style bits
                style = li["style"]
                # remove list-style-type: ...; (tolerate spacing)
                style2 = re.sub(r"(?i)\blist-style-type\s*:\s*[^;]+;?\s*", "", style).strip()
                if style2:
                    li["style"] = style2
                else:
                    del li["style"]

            # 2) Remove the explicit label span (1., 2., ...)
            # It is usually the first child span with classes ltx_tag and ltx_tag_item
            tag = li.find("span", class_=lambda c: c and "ltx_tag_item" in c.split())
            if tag and tag.get_text(strip=True).rstrip(".").isdigit():
                tag.decompose()

            # 3) (Optional) If the remaining structure starts with a block <div> that forces a new line,
            # let the browser handle it naturally; this is fine once native list markers are back.
            # No extra changes needed.

    return soup


def canvas_sanitize_html(html_text: str, css_texts: list[str]) -> str:
    # First inline CSS normally
    soup = BeautifulSoup(inline_css(html_text, css_texts), "html.parser")
    # Then fix LaTeXML numbering
    soup = fix_latexml_numbering_for_canvas(soup)
    return str(soup)


# -----------------------------
# UI
# -----------------------------
st.subheader("Options")
fix_numbering = st.checkbox(
    "Fix LaTeXML numbering for Canvas (recommended)",
    value=True,
    help="Converts LaTeXML numbered lists to native <ol>/<li> numbering so numbers stay on the same line in Canvas."
)

if html_file and css_files:
    output_name = make_inline_filename(html_file.name)

    if st.button("Create Canvas-safe HTML"):
        html_text = html_file.read().decode("utf-8", errors="replace")
        css_texts = [f.read().decode("utf-8", errors="replace") for f in css_files]

        if fix_numbering:
            output_html = canvas_sanitize_html(html_text, css_texts)
        else:
            output_html = inline_css(html_text, css_texts)

        st.success("Done! Your HTML is now self-contained.")

        st.download_button(
            label="Download standalone HTML",
            data=output_html,
            file_name=output_name,
            mime="text/html"
        )
