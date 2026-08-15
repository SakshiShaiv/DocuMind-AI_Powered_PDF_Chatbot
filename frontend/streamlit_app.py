import streamlit as st
import requests
from datetime import datetime




API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="DocuMind",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>

    .stApp {
        background: #080d17;
        color: #eef2f8;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 1.2rem;
        padding-bottom: 5rem;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* SIDEBAR */

    section[data-testid="stSidebar"] {
        background: #0d1420;
        border-right: 1px solid #202a3b;
    }

    section[data-testid="stSidebar"] .block-container {
        padding: 1.35rem 1rem;
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 25px;
        font-weight: 750;
        letter-spacing: -0.7px;
    }

    section[data-testid="stSidebar"] p {
        color: #8190a7;
    }

    section[data-testid="stSidebar"] h3 {
        color: #748198;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 22px;
        margin-bottom: 8px;
    }

    /* BUTTONS */

    .stButton > button {
        min-height: 42px;
        border-radius: 10px;
        border: 1px solid #29354a;
        background: #141c2a;
        color: #e8edf5;
        font-weight: 600;
    }

    .stButton > button:hover {
        border-color: #5c4bd8;
        background: #1b2435;
        color: white;
    }

    /* FILE UPLOADER */

    section[data-testid="stSidebar"]
    [data-testid="stFileUploader"] {
        background: #101722;
        border: 1px solid #202c3e;
        border-radius: 12px;
        padding: 7px;
    }

    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] {
        background: #101722;
        border: none;
    }

    /* HEADER */

    .top-title {
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -1.2px;
        margin-bottom: 0;
    }

    .top-subtitle {
        color: #8b98ab;
        font-size: 16px;
        margin-top: 3px;
    }

    /* WELCOME */

    .welcome-icon {
        font-size: 58px;
        text-align: center;
        margin-top: 45px;
        margin-bottom: 5px;
    }

    .welcome-title {
        text-align: center;
        font-size: 38px;
        font-weight: 800;
        letter-spacing: -1.3px;
    }

    .welcome-text {
        text-align: center;
        color: #8997ab;
        font-size: 16px;
        line-height: 1.65;
        max-width: 700px;
        margin: auto;
    }

    .source-label {
        color: #8996aa;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-top: 15px;
        margin-bottom: 7px;
    }

    [data-testid="stChatMessage"] {
        background: transparent;
        border: none;
    }

    [data-testid="stChatMessageContent"] {
        line-height: 1.65;
    }

    [data-testid="stChatInput"] {
        border-top: 1px solid #1e2938;
        padding-top: 10px;
    }

    @media (max-width: 900px) {

        .welcome-title {
            font-size: 30px;
        }

        .top-title {
            font-size: 28px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)




if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_document" not in st.session_state:
    st.session_state.selected_document = "All Documents"

if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False




def check_backend():

    try:

        response = requests.get(
            f"{API_URL}/documents",
            timeout=3
        )

        return response.status_code == 200

    except Exception:

        return False


def get_documents():

    try:

        response = requests.get(
            f"{API_URL}/documents",
            timeout=5
        )

        if response.status_code != 200:
            return []

        data = response.json()

        return data.get("documents", [])

    except Exception:

        return []



def process_question(question):

  

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "time": datetime.now().strftime("%H:%M"),
        }
    )

    params = {
        "question": question
    }

 

    if (
        st.session_state.selected_document
        != "All Documents"
    ):

        params["document"] = (
            st.session_state.selected_document
        )

    try:

        
        with st.spinner(
            "🔎 Searching your documents..."
        ):

            response = requests.get(
                f"{API_URL}/chat",
                params=params,
                timeout=180
            )

        result = response.json()

      
        if "error" in result:

            answer = f"⚠️ {result['error']}"
            sources = []

        else:

            answer = result.get(
                "answer",
                "No answer received."
            )

            sources = result.get(
                "sources",
                []
            )

    

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "time": datetime.now().strftime("%H:%M"),
            }
        )

    except requests.exceptions.ConnectionError:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "⚠️ **Backend Offline**\n\n"
                    "Please start FastAPI on port 8000."
                ),
                "sources": [],
                "time": datetime.now().strftime("%H:%M"),
            }
        )

    except requests.exceptions.Timeout:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "⚠️ The request took too long. "
                    "Please try again."
                ),
                "sources": [],
                "time": datetime.now().strftime("%H:%M"),
            }
        )

    except Exception as e:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"⚠️ Error: {e}",
                "sources": [],
                "time": datetime.now().strftime("%H:%M"),
            }
        )




backend_online = check_backend()
documents = get_documents()



with st.sidebar:

    

    st.title("✦ DocuMind")

    st.caption(
        "AI-powered document workspace"
    )

    st.divider()

  

    st.markdown("### WORKSPACE")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )

    st.caption(
        "PDF only • Max 200MB per file"
    )

    if uploaded_file:

        st.caption(
            f"📄 {uploaded_file.name}"
        )

        if st.button(
            "⬆️ Upload & Index",
            use_container_width=True
        ):

            with st.spinner(
                "Processing document..."
            ):

                try:

                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    }

                    response = requests.post(
                        f"{API_URL}/upload",
                        files=files,
                        timeout=180
                    )

                    result = response.json()

                    if "error" in result:

                        st.error(
                            result["error"]
                        )

                    else:

                        st.success(
                            "PDF indexed successfully!"
                        )

                        st.session_state.messages = []

                        st.rerun()

                except requests.exceptions.Timeout:

                    st.error(
                        "Upload timed out."
                    )

                except Exception as e:

                    st.error(
                        f"Upload failed: {e}"
                    )


    st.markdown("### DOCUMENTS")

    options = [
        "All Documents"
    ] + documents

    if (
        st.session_state.selected_document
        not in options
    ):

        st.session_state.selected_document = (
            "All Documents"
        )

    selected_document = st.selectbox(
        "Choose document",
        options,
        index=options.index(
            st.session_state.selected_document
        ),
        label_visibility="collapsed"
    )

    st.session_state.selected_document = (
        selected_document
    )

    if documents:

        st.caption(
            f"{len(documents)} document"
            f"{'s' if len(documents) != 1 else ''}"
        )

        for doc in documents:

            st.markdown(
                f"📄 **{doc}**"
            )

    else:

        st.caption(
            "No documents uploaded yet."
        )



    st.markdown("### SYSTEM")

    if backend_online:

        st.success(
            "● Backend Connected"
        )

        st.caption(
            "All systems operational"
        )

    else:

        st.error(
            "● Backend Offline"
        )

        st.caption(
            "Start FastAPI on port 8000"
        )


    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        if not st.session_state.confirm_clear:

            st.session_state.confirm_clear = True

        else:

            st.session_state.messages = []
            st.session_state.confirm_clear = False

        st.rerun()

    if st.session_state.confirm_clear:

        st.warning(
            "Click again to confirm."
        )

    st.caption(
        "✦ DocuMind v1.0.0"
    )



header_left, header_right = st.columns(
    [6, 1]
)

with header_left:

    st.markdown(
        '<div class="top-title">📚 DocuMind</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="top-subtitle">'
        'Chat with your documents using AI'
        '</div>',
        unsafe_allow_html=True
    )

with header_right:

    if backend_online:

        st.success("● Ready")

    else:

        st.error("● Offline")


st.divider()




if (
    st.session_state.selected_document
    != "All Documents"
):

    st.info(
        f"📄 Currently chatting with: "
        f"**{st.session_state.selected_document}**"
    )




if not st.session_state.messages:

    st.markdown(
        '<div class="welcome-icon">📖</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="welcome-title">'
        'Ask questions about your documents.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="welcome-text">'
        'Upload a PDF and ask questions about its content. '
        'DocuMind retrieves the most relevant sections '
        'from your documents and generates grounded answers.'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    st.info(
        "💡 Upload a PDF from the sidebar, "
        "then ask any question about its content."
    )




for message in st.session_state.messages:

    role = message["role"]

    with st.chat_message(role):

        st.caption(
            message.get(
                "time",
                ""
            )
        )

        st.markdown(
            message.get(
                "content",
                ""
            )
        )

        sources = message.get(
            "sources",
            []
        )

        if (
            role == "assistant"
            and sources
        ):

            st.markdown(
                '<div class="source-label">'
                '📑 SOURCES'
                '</div>',
                unsafe_allow_html=True
            )

            seen = set()

            for source in sources:

                filename = source.get(
                    "source",
                    "Unknown"
                )

                page = source.get(
                    "page",
                    "?"
                )

                key = (
                    filename,
                    page
                )

                if key in seen:
                    continue

                seen.add(key)

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"📄 **{filename}**"
                    )

                    st.caption(
                        f"Page {page}"
                    )




question = st.chat_input(
    "Ask anything about your documents..."
)

if question:

    process_question(question)

    st.rerun()