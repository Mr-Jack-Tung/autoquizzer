from .custom_components import TrafilaturaHTMLConverter, QuizParser
from haystack.components.fetchers import LinkContentFetcher
# from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder
from haystack.components.websearch.serper_dev import SerperDevWebSearch

from haystack.utils import Secret
from haystack import Pipeline


quiz_generation_template = """Given the following text, create 5 multiple choice quizzes in JSON format.
Each question should have 4 different options, and only one of them should be correct.
The options should be unambiguous.
Each option should begin with a letter followed by a period and a space (e.g., "a. option").
The question should also briefly mention the general topic of the text so that it can be understood in isolation.
Each question should not give hints to answer the other questions.
Include challenging questions, which require reasoning.

respond with JSON only, no markdown or descriptions.

example JSON format you should absolutely follow:
{"topic": "a sentence explaining the topic of the text",
 "questions":
  [
    {
      "question": "text of the question",
      "options": ["a. 1st option", "b. 2nd option", "c. 3rd option", "d. 4th option"],
      "right_option": "c"  # letter of the right option ("a" for the first, "b" for the second, etc.)
    }, ...
  ]
}

text:
{% for doc in documents %}{{ doc.content|truncate(4000) }}{% endfor %}
"""


quiz_generation_pipeline = Pipeline()
quiz_generation_pipeline.add_component("link_content_fetcher", LinkContentFetcher())
quiz_generation_pipeline.add_component("html_converter", TrafilaturaHTMLConverter())
quiz_generation_pipeline.add_component(
    "prompt_builder", PromptBuilder(template=quiz_generation_template)
)

from haystack_integrations.components.generators.ollama import OllamaGenerator

quiz_generation_pipeline.add_component(
    "generator",
    OllamaGenerator(model="mistral",
                    url = "http://localhost:11434/api/generate",
                    generation_kwargs={
                      "num_predict": 1000,
                      "temperature": 0.5,
                      "top_p": 1
                      }),
    # OpenAIGenerator(
    #     api_key=Secret.from_env_var("GROQ_API_KEY"),
    #     api_base_url="https://api.groq.com/openai/v1",
    #     model="llama3-8b-8192",
    #     generation_kwargs={"max_tokens": 1000, "temperature": 0.5, "top_p": 1},
    # ),
)
quiz_generation_pipeline.add_component("quiz_parser", QuizParser())

quiz_generation_pipeline.connect("link_content_fetcher", "html_converter")
quiz_generation_pipeline.connect("html_converter", "prompt_builder")
quiz_generation_pipeline.connect("prompt_builder", "generator")
quiz_generation_pipeline.connect("generator", "quiz_parser")


closed_book_template = """Answer the following question, specifying one of the options.
The topic is: {{ topic }}.

In the answer, just specify the letter corresponding to the option.
If you don't know the answer, just provide your best guess and do not provide any reasoning.

For example, if you think the answer is the first option, just write "a".
If you think the answer is the second option, just write "b", and so on.

question: {{ question["question"] }}
options: {{ question["options"] }}

chosen option (a, b, c, or d):
"""

closed_book_answer_pipeline = Pipeline()
closed_book_answer_pipeline.add_component("prompt_builder", PromptBuilder(template=closed_book_template))
closed_book_answer_pipeline.add_component(
    "generator",
    OllamaGenerator(model="mistral",
                    url = "http://localhost:11434/api/generate",
                    generation_kwargs={
                      "num_predict": 1000,
                      "temperature": 0.5,
                      "top_p": 1
                      }),
    # OpenAIGenerator(
    #     api_key=Secret.from_env_var("GROQ_API_KEY"),
    #     api_base_url="https://api.groq.com/openai/v1",
    #     model="llama3-8b-8192",
    #     generation_kwargs={"max_tokens": 5, "temperature": 0, "top_p": 1},
    # ),
)
closed_book_answer_pipeline.connect("prompt_builder", "generator")


web_rag_template = """Answer the question about "{{topic}}", using your knowledge and the snippets extracted from the web.

In the answer, just specify the letter corresponding to the option.
If you don't know the answer, just provide your best guess and do not provide any reasoning.

For example, if you think the answer is the first option, just write "a".
If you think the answer is the second option, just write "b", and so on.

question: {{ question["question"] }}
options: {{ question["options"] }}

Snippets:
{% for doc in documents %}
- snippet: "{{doc.content}}"
{% endfor %}

chosen option (a, b, c, or d):
"""


from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from haystack import component
from typing import List
from haystack import Document

# https://docs.haystack.deepset.ai/docs/custom-components
# https://docs.haystack.deepset.ai/reference/websearch-api
# https://python.langchain.com/v0.1/docs/integrations/tools/wikipedia/

@component
class WikiSearch:
    """
    Search the world's information to help you find exactly what you're looking.
    """

    @component.output_types(documents=List[Document])
    def run(self, query:str):
        print("\nquery:",query)

        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=4000))
        results = wikipedia.run(query)
        pages = results.split("\n\n")

        documents = []
        for page in pages:
            document = Document(content=str(page.split("Summary: ")[1]))
            documents.append(document)

        # return results
        return {"documents": documents}


web_rag_pipeline = Pipeline()
# web_rag_pipeline.add_component("websearch", SerperDevWebSearch(top_k=3))
web_rag_pipeline.add_component("websearch", WikiSearch())
web_rag_pipeline.add_component("prompt_builder", PromptBuilder(template=web_rag_template))
web_rag_pipeline.add_component(
    "generator",
    OllamaGenerator(model="mistral",
                    url = "http://localhost:11434/api/generate",
                    generation_kwargs={
                      "num_predict": 1000,
                      "temperature": 0.5,
                      "top_p": 1
                      }),
    # OpenAIGenerator(
    #     api_key=Secret.from_env_var("GROQ_API_KEY"),
    #     api_base_url="https://api.groq.com/openai/v1",
    #     model="llama3-8b-8192",
    #     generation_kwargs={"max_tokens": 5, "temperature": 0, "top_p": 1},
    # ),
)
web_rag_pipeline.connect("websearch.documents", "prompt_builder.documents")
web_rag_pipeline.connect("prompt_builder", "generator")
