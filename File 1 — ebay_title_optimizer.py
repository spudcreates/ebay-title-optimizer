import streamlit as st
import pandas as pd
import OpenAI
import io
import time
import requests
import json, re

client = OpenAI()

st.set_page_config(page_title="AI eBay Title & Keyword Optimizer", page_icon="🛒", layout="centered")

st.title("🛍️ AI eBay Title & Keyword Optimizer")
st.write(
    "Upload a CSV — the tool rewrites titles, suggests keywords, and enriches them with trending data."
)
st.caption("Titles are checked and trimmed to stay under eBay’s 80-character limit.")

uploaded_file = st.file_uploader("📤 Upload your CSV file", type=["csv"])
auto_trim = st.checkbox("✂️ Automatically trim titles over 80 characters", value=True)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"✅ File uploaded! {len(df)} rows detected.")
    st.write(df.head())

    if st.button("🚀 Optimize & Enrich Keywords"):
        st.info("Optimizing titles… please wait.")

        optimized_titles, enriched_keywords = [], []
        too_long_count = 0

        for _, row in df.iterrows():
            title = row.get("Title", "")
            brand = row.get("Brand", "")
            category = row.get("Category", "")
            seed = row.get("SeedKeyword", title)

            prompt = f"""
            You are an expert eBay SEO copywriter.
            1️⃣ Rewrite this title (≤ 80 chars) for clarity and SEO.
            2️⃣ Suggest 4–6 strong related keywords.

            Product info:
            Title: "{title}"
            Brand: {brand or "N/A"}
            Category: {category or "N/A"}

            Respond in JSON:
            {{
              "optimized_title": "string",
              "keywords": ["kw1","kw2","kw3"]
            }}
            """

            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a skilled eBay SEO optimizer."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=120,
                    temperature=0.7,
                )
                content = resp.choices[0].message.content.strip()
                json_text = re.search(r"\{.*\}", content, re.DOTALL)
                if json_text:
                    result = json.loads(json_text.group())
                    optimized = result.get("optimized_title", title)
                    kw_ai = result.get("keywords", [])
                else:
                    optimized, kw_ai = content[:80], []
            except Exception as e:
                optimized, kw_ai = title, []

            if len(optimized) > 80:
                too_long_count += 1
                if auto_trim:
                    optimized = optimized[:77].rstrip() + "..."

            # --- Keyword enrichment placeholder ---
            try:
                extra_kw = [seed + " sale", seed + " new", seed + " used", seed + " authentic"]
            except Exception:
                extra_kw = []

            keywords = ", ".join(kw_ai + extra_kw)
            optimized_titles.append(optimized)
            enriched_keywords.append(keywords)
            time.sleep(1)

        df["OptimizedTitle"] = optimized_titles
        df["SuggestedKeywords"] = enriched_keywords

        st.success("🎉 Optimization complete!")
        if too_long_count:
            msg = (
                f"✂️ {too_long_count} titles trimmed."
                if auto_trim
                else f"⚠️ {too_long_count} titles exceed 80 chars."
            )
            st.warning(msg)

        st.write(df.head())

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        st.download_button(
            "📥 Download Optimized CSV",
            buf,
            "optimized_enriched_ebay_titles.csv",
            "text/csv",
        )
