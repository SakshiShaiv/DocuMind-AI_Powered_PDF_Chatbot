from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import json
import os


DOCUMENTS_FILE = "documents.json"
HASH_FILE = "uploaded_files.json"



def process_pdf(file_path):

    reader = PdfReader(file_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    documents = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        page_text = page.extract_text()

        if not page_text:
            continue

        page_documents = splitter.create_documents(
            [page_text]
        )

        for doc in page_documents:

            doc.metadata["page"] = page_number

            doc.metadata["source"] = (
                os.path.basename(file_path)
            )

        documents.extend(
            page_documents
        )

    return documents, len(reader.pages)




def save_documents(documents):

    data = []

    for doc in documents:

        data.append(
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
        )

    with open(
        DOCUMENTS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )



def load_documents():

    if not os.path.exists(
        DOCUMENTS_FILE
    ):

        return []

    with open(
        DOCUMENTS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    documents = []

    for item in data:

        if (
            isinstance(item, dict)
            and "page_content" in item
        ):

            documents.append(
                Document(
                    page_content=item[
                        "page_content"
                    ],
                    metadata=item.get(
                        "metadata",
                        {}
                    )
                )
            )

    return documents


def load_uploaded_files():

    if not os.path.exists(
        HASH_FILE
    ):

        return set()

    with open(
        HASH_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return set(data)




def save_uploaded_files(
    uploaded_files
):

    with open(
        HASH_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            list(uploaded_files),
            f,
            indent=2
        )