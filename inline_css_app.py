import re
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="Inline CSS for Canvas", layout="centered")

st.title("HTML + CSS → Canvas-safe HTML")
st.markdown(
    """
This tool embeds external CSS files directly into an HTML file
so it will display correctly when uploaded to Canvas.
App written by ChatGPT.
"""
)

html_file = st.file_uploader("Upload HTML file", type=["html", "htm"])

css_files = st.file_uploader(
    "Upload CSS file(s)", type=["css"], accept_multiple_files=True
)

# ---------------------------------------------------
# Core CSS inlining
# ---------------------------------------------------

def inline_css(html_text: str, css_texts: list[str]) -> str:
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove external stylesheet links
    for link in soup.find_all("link", rel="stylesheet"):
        link.decompose()

    # Ensure <head> exists
    if soup.head is None:
        if soup.html is None:
            html_tag = soup.new_tag("html")
            for node in list(soup.contents):
                html_tag.append(node.extract())
            soup.append(html_tag)

        head = soup.new_tag("head")
        soup.html.insert(0, head)
    else:
        head = soup.head

    # Append CSS into a <style> tag
    style = soup.new_tag("style")
    style.string = "\n\n".join(css_texts)
    head.append(style)

    return str(soup)


# ---------------------------------------------------
# Fix LaTeXML numbering (Canvas-safe)
# ---------------------------------------------------

def fix_latexml_numbering_for_canvas(soup: BeautifulSoup) -> BeautifulSoup:
    for ol in soup.select("ol.ltx_enumerate"):
        for li in ol.select("li.ltx_item"):

            # Remove list-style-type:none
            if li.has_attr("style"):
                style = li["style"]
                style2 = re.sub(
                    r"(?i)\blist-style-type\s*:\s*[^;]+;?\s*",
                    "",
                    style
                ).strip()

                if style2:
                    li["style"] = style2
                else:
                    del li["style"]

            # Remove explicit LaTeXML number span
            tag = li.find("span", class_=lambda c: c and "ltx_tag_item" in c)
            if tag and tag.get_text(strip=True).rstrip(".").isdigit():
                tag.decompose()

    return soup


# ---------------------------------------------------
# Remove LaTeXML footer + mascot image
# ---------------------------------------------------

def remove_latexml_footer(soup: BeautifulSoup) -> BeautifulSoup:
    footer = soup.find("footer", class_="ltx_page_footer")

    if footer:
        # Remove only embedded base64 image(s)
        for img in footer.find_all("img"):
            img.decompose()

        # Option A: Remove entire footer (cleanest)
        footer.decompose()

        # If instead you want to keep the link text,
        # comment out footer.decompose() above
        # and just leave the <a> element intact.

    return soup


# ---------------------------------------------------
# Combined processing
# ---------------------------------------------------

def process_html(html_text: str, css_texts: list[str]) -> str:
    # First inline CSS
    soup = BeautifulSoup(inline_css(html_text, css_texts), "html.parser")

    # Then fix numbering
    soup = fix_latexml_numbering_for_canvas(soup)

    # Then remove footer + mascot
    soup = remove_latexml_footer(soup)

    return str(soup)


def make_inline_filename(original_name: str, suffix="_inline") -> str:
    if "." in original_name:
        base, ext = original_name.rsplit(".", 1)
        return f"{base}{suffix}.{ext}"
    return f"{original_name}{suffix}.html"


# ---------------------------------------------------
# UI
# ---------------------------------------------------

if html_file and css_files:
    output_name = make_inline_filename(html_file.name)

    if st.button("Create Canvas-safe HTML"):
        html_text = html_file.read().decode("utf-8", errors="replace")
        css_texts = [f.read().decode("utf-8", errors="replace") for f in css_files]

        output_html = process_html(html_text, css_texts)

        st.success("Done! Your HTML is now Canvas-safe.")

        st.download_button(
            label="Download standalone HTML",
            data=output_html,
            file_name=output_name,
            mime="text/html"
        )
        