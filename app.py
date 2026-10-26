
import streamlit as st
import html

st.set_page_config(
    page_title="Google Forms",
    layout="wide",
)

# Page styling
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    h1 {
        font-size: 28px !important;
        font-weight: 500 !important;
        color: #202124;
    }

    h2, h3 {
        color: #202124;
    }

    /* Keep the search bar compact */
    div[data-testid="stTextInput"] {
        max-width: 350px;
        width: 100%;
    }

    
div[data-testid="stTextInput"] input {
    box-sizing: border-box;
    width: 100%;
    height: 42px;
    border-radius: 24px;
    border: 1px solid #dadce0 !important;
    padding: 10px 16px;
    background-color: #f1f3f4 !important;
    color: #202124 !important;
    -webkit-text-fill-color: #202124 !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #5f6368 !important;
    -webkit-text-fill-color: #5f6368 !important;
    opacity: 1 !important;
}

    /* Compact plain form cards */
    
/* Google Forms-style cards */
.form-card {
    width: 100%;
    max-width:280px;
    height: 250px;
    box-sizing: border-box;
    border: 1px solid #dadce0;
    border-radius: 8px;
    background: #ffffff;
    color: #202124;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-card:hover {
    border-color: #673ab7;
    box-shadow: 0 1px 3px rgba(60, 64, 67, 0.2);
}

/* Preview area */
.form-preview {
    height: 120px;
    flex-shrink:0;
    background: #ffffff;
    border-bottom: 1px solid #dadce0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.form-preview-icon {
    width: 58px;
    height: 72px;
    border: 2px solid #673ab7;
    border-radius: 3px;
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 8px;
    padding: 10px;
}

.form-preview-icon span {
    display: block;
    height: 3px;
    border-radius: 2px;
    background: #673ab7;
}

/* Card details */
.form-details {
    padding: 18px 12px 12px;
    display: flex;
    flex-direction: column;
    gap: 7px;
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.form-name {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.4;
    color: #202124;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.form-meta {
    font-size: 12px;
    color: #5f6368;
}
  </style>
    """,
    unsafe_allow_html=True,
)

# Page heading
st.title("Google Forms")

# Search bar
search_query = st.text_input(
    "Search forms",
    placeholder="Search forms",
    label_visibility="collapsed",
)

st.subheader("Recent forms")

# Temporary sample data


from backend import connect_google_account, fetch_forms

if st.button("Connect Google Account"):
    try:
        connect_google_account()
        st.rerun()
    except Exception as error:
        st.error(f"Google authorization failed: {error}")

if "google_credentials" not in st.session_state:
    st.info("Connect your Google account to view your forms.")
    st.stop()

try:
    google_forms = fetch_forms()

    forms = [
        {
            "name": form.get("name", "Untitled form"),
            "modified": form.get("modifiedTime", ""),
            "id": form["id"],
            "link": form.get("webViewLink")
            or f"https://docs.google.com/forms/d/{form['id']}/edit",
        }
        for form in google_forms
    ]

except Exception as error:
    st.error(f"Could not retrieve Google Forms: {error}")
    st.stop()

filtered_forms = [
    form for form in forms
    if search_query.lower() in form["name"].lower()
]

if filtered_forms:
    columns_per_row = 4

    for start in range(0, len(filtered_forms), columns_per_row):
        row_forms = filtered_forms[start:start + columns_per_row]
        columns = st.columns(columns_per_row, gap="small")

        for col, form in zip(columns, row_forms):
            with col:
                safe_name = html.escape(form["name"])
                safe_modified = html.escape(form["modified"])
                safe_link = html.escape(form["link"], quote=True)

                
                st.markdown(
            f"""
            <a href="{safe_link}"
               target="_blank"
               style="text-decoration:none;color:inherit;display:block;">
                <div class="form-card">
                    <div class="form-preview">
                        <div class="form-preview-icon">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                    <div class="form-details">
                        <div class="form-name">{safe_name}</div>
                        <div class="form-meta">{safe_modified}</div>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

else:
    if not forms:
        st.info("No Google Forms were found in this account.")
    else:
        st.info("No forms match your search.")


