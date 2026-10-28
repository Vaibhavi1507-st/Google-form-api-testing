
import streamlit as st
import html
import os
import streamlit.components.v1 as components
from backend import (
    complete_authorization,
    fetch_forms,
    fetch_form_responses,
    save_responses_to_json,
    get_authorization_url,
    get_credentials,
    fetch_form_questions,
)
clickable_cards = components.declare_component(
    "clickable_cards",
    path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "clickable_card",
    ),
)


st.set_page_config(
    page_title="Google Forms",
    layout="wide",
)
selected_form_id = st.session_state.get("selected_form_id")
# Handle Google's redirect back to the app.

query_params = st.query_params

if query_params.get("code"):
    try:
        complete_authorization(
            code=query_params["code"],
            returned_state=query_params.get("state", ""),
        )
        st.query_params.clear()
        st.rerun()
    except Exception as error:
        st.error(f"Google authorization failed: {error}")
        st.stop()

# Show the sign-in button if the user isn't connected.

if not get_credentials():
    if st.button("Connect Google Account"):
        authorization_url = get_authorization_url()
        st.markdown(
            f'<meta http-equiv="refresh" content="0;url={authorization_url}">',
            unsafe_allow_html=True,
        )

    st.info("Connect your Google account to view your forms.")
    st.stop()


# The user is connected; continue to your existing form-listing code.
try:
    forms = fetch_forms()
except Exception as error:
    st.error(f"Could not retrieve Google Forms: {error}")
    st.stop()




if selected_form_id:
    selected_form = next(
        (
            form for form in forms
            if form.get("id") == selected_form_id
        ),
        None,
    )

    if not selected_form:
        st.error("The selected form was not found.")
        st.stop()

    try:
        responses = fetch_form_responses(selected_form_id)

        json_path = save_responses_to_json(
            form_id=selected_form_id,
            form_name=selected_form.get("name", "Untitled form"),
            responses=responses,
        )

        st.title(selected_form.get("name", "Untitled form"))
        st.success("Responses saved to JSON successfully.")
        st.write(f"Total responses: {len(responses)}")

        # Convert responses into rows for the UI grid
        table_rows = []

        questions = fetch_form_questions(selected_form_id)

        
        table_rows = []
        questions = fetch_form_questions(selected_form_id)

        for response in responses:
            row = {
                "Response ID": response.get("responseId", ""),
                "Submitted at": response.get("lastSubmittedTime", ""),
            }

            for question_id, answer_data in response.get("answers", {}).items():
                question_title = questions.get(question_id, question_id)

                # Handle uploaded files, such as resumes
                uploaded_files = answer_data.get(
                    "fileUploadAnswers", {}
                ).get("answers", [])

                if uploaded_files:
                    for index, uploaded_file in enumerate(uploaded_files, start=1):
                        file_id = uploaded_file.get("fileId", "")
                        if file_id:
                            row[f"{question_title} ({index})"] = (
                                f"https://drive.google.com/file/d/{file_id}/view"
                            )
                else:
                    # Handle normal text answers
                    values = [
                        answer.get("value", "")
                        for answer in answer_data.get(
                            "textAnswers", {}
                        ).get("answers", [])
                    ]
                    row[question_title] = ", ".join(values)

            table_rows.append(row)

        if table_rows:
            st.subheader("Form responses")

            # Make Google Drive file URLs clickable
            column_config = {}
            for column in table_rows[0].keys():
                if any(
                    str(item.get(column, "")).startswith(
                        "https://drive.google.com/file/d/"
                    )
                    for item in table_rows
                ):
                    column_config[column] = st.column_config.LinkColumn(
                        column,
                        display_text="View file",
                    )

            st.dataframe(
                table_rows,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No responses have been submitted to this form yet.")

    except Exception as error:
        st.error(f"Could not fetch or save responses: {error}")
        st.stop()

    st.stop()


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
    position: relative;
    cursor:pointer;
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
# Show the form list only when no form is selected.
if not selected_form_id:
    st.title("Google Forms")

# Search bar
search_query = st.text_input(
    "Search forms",
    placeholder="Search forms",
    label_visibility="collapsed",
)

st.subheader("Recent forms")

# Temporary sample data


filtered_forms = [
    {
        "id": form.get("id", ""),
        "name": form.get("name", "Untitled form"),
        "link": form.get("webViewLink", ""),
        "modified": form.get("modifiedTime", ""),
    }
    for form in forms
    if search_query.lower() in form.get("name", "").lower()
    and form.get("webViewLink")
]

if "selected_form" not in st.session_state:
    st.session_state.selected_form = None




if filtered_forms:
    selected_form_id = clickable_cards(
        forms=filtered_forms,
        key="google_forms_cards",
    )

    if selected_form_id:
        st.session_state["selected_form_id"] = selected_form_id
        st.rerun()

else:
    if search_query:
        st.info("No forms match your search. Try a different name.")
    else:
        st.info(
            "No Google Forms found. Create a form in Google Forms, "
            "then refresh this page."
        )
        st.link_button("Open Google Forms", "https://forms.google.com")
