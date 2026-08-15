from fastapi import FastAPI, UploadFile, File

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)

from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv

from services.document_processor import (
    process_pdf,
    save_documents,
    load_documents,
    load_uploaded_files,
    save_uploaded_files
)

import os
import hashlib




load_dotenv()

app = FastAPI()




llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=os.getenv(
        "GOOGLE_API_KEY"
    )
)




embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2",
    google_api_key=os.getenv(
        "GOOGLE_API_KEY"
    )
)




FAISS_FOLDER = "faiss_index"

vector_store = None




all_documents = load_documents()




uploaded_files = load_uploaded_files()



if os.path.exists(
    FAISS_FOLDER
):

    try:

        vector_store = FAISS.load_local(
            FAISS_FOLDER,
            embeddings,
            allow_dangerous_deserialization=True
        )

        print(
            "Existing FAISS index loaded."
        )

    except Exception as e:

        print(
            "Could not load FAISS index:"
        )

        print(e)




@app.get("/")
def home():

    return {
        "message":
        "PDF Chatbot Backend is running!"
    }





@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    global vector_store
    global all_documents
    global uploaded_files

    try:

       

        if file.content_type != "application/pdf":

            return {
                "error":
                "Please upload a PDF file."
            }

      

        content = await file.read()

        

        file_hash = hashlib.sha256(
            content
        ).hexdigest()

       

        if file_hash in uploaded_files:

            return {
                "error":
                "This PDF has already been uploaded."
            }

     

        os.makedirs(
            "uploads",
            exist_ok=True
        )

        original_filename = file.filename

        file_path = os.path.join(
            "uploads",
            original_filename
        )

       

        if os.path.exists(file_path):

            name, ext = os.path.splitext(
                original_filename
            )

            counter = 1

            while os.path.exists(
                file_path
            ):

                new_filename = (
                    f"{name}_{counter}{ext}"
                )

                file_path = os.path.join(
                    "uploads",
                    new_filename
                )

                counter += 1

      

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(content)

        print(
            "PDF temporarily saved:",
            file_path
        )

    

        documents, total_pages = process_pdf(
            file_path
        )

        print(
            "Pages:",
            total_pages
        )

        print(
            "Chunks:",
            len(documents)
        )

      

        all_documents.extend(
            documents
        )

        save_documents(
            all_documents
        )

       

        if vector_store is None:

            print(
                "Creating new FAISS index..."
            )

            vector_store = FAISS.from_documents(
                documents,
                embeddings
            )

        else:

            print(
                "Adding documents to existing FAISS..."
            )

            vector_store.add_documents(
                documents
            )

       

        vector_store.save_local(
            FAISS_FOLDER
        )

        print(
            "FAISS saved successfully."
        )

   

        uploaded_files.add(
            file_hash
        )

        save_uploaded_files(
            uploaded_files
        )


        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

            print(
                "Temporary PDF deleted."
            )

       

        return {

            "filename":
                original_filename,

            "pages":
                total_pages,

            "total_chunks":
                len(documents),

            "message":
                "PDF uploaded and indexed successfully!"

        }

    except Exception as e:

        print(
            "UPLOAD ERROR:",
            repr(e)
        )

        return {
            "error":
            str(e)
        }




@app.get("/documents")
def get_documents():

    try:

        documents = []

        for doc in all_documents:

            if not hasattr(
                doc,
                "metadata"
            ):

                continue

            source = doc.metadata.get(
                "source",
                ""
            )

            filename = os.path.basename(
                source
            )

            if (
                filename
                and filename not in documents
            ):

                documents.append(
                    filename
                )

        return {

            "total_documents":
                len(documents),

            "documents":
                documents

        }

    except Exception as e:

        return {
            "error":
            str(e)
        }




@app.get("/chat")
def chat(
    question: str,
    document: str | None = None
):

    global vector_store
    global all_documents

   

    if vector_store is None:

        return {
            "error":
            "Please upload a PDF first."
        }

    try:

     

        if document is None:

            relevant_docs = (
                vector_store.similarity_search(
                    question,
                    k=3
                )
            )

        else:

          

            selected_documents = [

                doc

                for doc in all_documents

                if hasattr(
                    doc,
                    "metadata"
                )

                and os.path.basename(
                    doc.metadata.get(
                        "source",
                        ""
                    )
                ).lower()
                == document.lower()

            ]

            if not selected_documents:

                return {
                    "error":
                    "Document not found."
                }

           

            all_results = (
                vector_store.similarity_search(
                    question,
                    k=10
                )
            )

           

            relevant_docs = [

                doc

                for doc in all_results

                if os.path.basename(
                    doc.metadata.get(
                        "source",
                        ""
                    )
                ).lower()
                == document.lower()

            ][:3]

           

            if not relevant_docs:

                relevant_docs = (
                    selected_documents[:3]
                )

       

        context = "\n\n".join(

            doc.page_content

            for doc in relevant_docs

        )


        prompt = f"""
You are DocuMind, an AI document question-answering assistant.

Answer the user's question using ONLY the provided document context.

Rules:
- Do not use outside knowledge.
- Do not make up information.
- If the answer is not available in the context,
  say exactly:

"I don't know based on the uploaded documents."

- Give a clear and concise answer.

Document Context:
----------------
{context}
----------------

User Question:
{question}

Answer:
"""

      

        response = llm.invoke(
            prompt
        )

        answer = response.content


        if isinstance(
            answer,
            list
        ):

            answer = "".join(

                item.get(
                    "text",
                    ""
                )

                for item in answer

                if item.get(
                    "type"
                ) == "text"

            )

        sources = []

        for doc in relevant_docs:

            sources.append(

                {
                    "page":
                        doc.metadata.get(
                            "page"
                        ),

                    "source":
                        os.path.basename(
                            doc.metadata.get(
                                "source",
                                ""
                            )
                        )
                }

            )

        

        return {

            "question":
                question,

            "answer":
                answer,

            "sources":
                sources

        }

    except Exception as e:

        print(
            "CHAT ERROR:",
            repr(e)
        )

        return {
            "error":
            str(e)
        }