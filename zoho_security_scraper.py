import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.units import mm
from urllib.parse import urljoin
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

URL = "https://www.zoho.com/security.html"
OUTPUT_PDF = "Zoho_Security_Information.pdf"


# ============================================================
# 1. DOWNLOAD WEBPAGE
# ============================================================

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    )
}

print("[1/5] Downloading Zoho Security page...")

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()

print("      Download successful.")
print(f"      HTTP Status: {response.status_code}")


# ============================================================
# 2. PARSE HTML
# ============================================================

print("[2/5] Parsing webpage...")

soup = BeautifulSoup(response.text, "html.parser")


# Remove elements that aren't part of the security content
for element in soup([
    "script",
    "style",
    "noscript",
    "iframe",
    "svg"
]):
    element.decompose()


# Try to locate the main article/content
main = (
    soup.find("main")
    or soup.find("article")
    or soup.find("div", class_="content")
)


if main is None:
    main = soup.body


# ============================================================
# 3. EXTRACT SECURITY INFORMATION
# ============================================================

print("[3/5] Extracting security information...")

content = []

# Track already-used text to reduce duplicate navigation text
seen = set()

for element in main.find_all(
    ["h1", "h2", "h3", "h4", "p", "li"]
):

    text = element.get_text(
        " ",
        strip=True
    )

    if not text:
        continue

    # Normalize spaces
    text = " ".join(text.split())

    # Remove duplicate content
    if text in seen:
        continue

    seen.add(text)

    tag = element.name

    if tag == "h1":
        content.append(("title", text))

    elif tag == "h2":
        content.append(("heading1", text))

    elif tag == "h3":
        content.append(("heading2", text))

    elif tag == "h4":
        content.append(("heading3", text))

    elif tag == "li":
        content.append(("bullet", text))

    else:
        content.append(("paragraph", text))


print(f"      Extracted {len(content)} content blocks.")


# ============================================================
# 4. CREATE PDF
# ============================================================

print("[4/5] Creating PDF...")

doc = SimpleDocTemplate(
    OUTPUT_PDF,
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm
)

styles = getSampleStyleSheet()


# ---------- Custom styles ----------

title_style = ParagraphStyle(
    "CustomTitle",
    parent=styles["Title"],
    fontSize=22,
    leading=28,
    alignment=TA_CENTER,
    spaceAfter=15
)

subtitle_style = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    alignment=TA_CENTER,
    spaceAfter=20
)

heading1_style = ParagraphStyle(
    "Heading1Custom",
    parent=styles["Heading1"],
    fontSize=16,
    leading=20,
    spaceBefore=14,
    spaceAfter=8
)

heading2_style = ParagraphStyle(
    "Heading2Custom",
    parent=styles["Heading2"],
    fontSize=13,
    leading=17,
    spaceBefore=10,
    spaceAfter=6
)

heading3_style = ParagraphStyle(
    "Heading3Custom",
    parent=styles["Heading3"],
    fontSize=11,
    leading=15,
    spaceBefore=8,
    spaceAfter=4
)

paragraph_style = ParagraphStyle(
    "ParagraphCustom",
    parent=styles["BodyText"],
    fontSize=9.5,
    leading=14,
    spaceAfter=7
)

bullet_style = ParagraphStyle(
    "BulletCustom",
    parent=styles["BodyText"],
    fontSize=9.5,
    leading=14,
    leftIndent=15,
    firstLineIndent=-8,
    spaceAfter=4
)


# ============================================================
# 5. BUILD PDF CONTENT
# ============================================================

story = []


# Cover
story.append(
    Paragraph(
        "Zoho Security Information",
        title_style
    )
)

story.append(
    Paragraph(
        "Scraped from the official Zoho Security Whitepaper",
        subtitle_style
    )
)

story.append(
    Paragraph(
        f"Source: {URL}",
        subtitle_style
    )
)

story.append(
    Paragraph(
        f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        subtitle_style
    )
)

story.append(Spacer(1, 10))

story.append(
    Paragraph(
        "This document contains the security information "
        "extracted from the Zoho Security webpage.",
        paragraph_style
    )
)

story.append(PageBreak())


# Add extracted content
for content_type, text in content:

    # Escape special XML characters for ReportLab
    text = (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    if content_type == "title":

        story.append(
            Paragraph(
                text,
                title_style
            )
        )

    elif content_type == "heading1":

        story.append(
            Paragraph(
                text,
                heading1_style
            )
        )

    elif content_type == "heading2":

        story.append(
            Paragraph(
                text,
                heading2_style
            )
        )

    elif content_type == "heading3":

        story.append(
            Paragraph(
                text,
                heading3_style
            )
        )

    elif content_type == "bullet":

        story.append(
            Paragraph(
                "• " + text,
                bullet_style
            )
        )

    elif content_type == "paragraph":

        story.append(
            Paragraph(
                text,
                paragraph_style
            )
        )


# Build PDF
doc.build(story)


# ============================================================
# FINISHED
# ============================================================

print("[5/5] PDF creation completed!")

print()
print("=" * 60)
print("SUCCESS")
print("=" * 60)
print(f"PDF created: {OUTPUT_PDF}")
print("=" * 60)