## Update: 18 May 2024
- File: pipelines.py
- - Replace OpenAIGenerator by OllamaGenerator
- - Replace SerperDevWebSearch by WikiSearch Custom Component

Hôm nay test thử cái AutoQuizzer cho LLM nó tự sinh ra đề bài và làm bài quiz. Cái này khá hay khi ứng dụng trong lĩnh vực giáo dục, thầy cô giáo có thể dùng em nó để tạo ra bộ câu hỏi trắc nghiệm, kiểm tra kiến thức khá hay. AutoQuizzer có thể tạo bài quiz với nội dung là một bài trên Wiki mà không có sự hỗ trợ thêm dữ liệu bên ngoài thì em nó trả lời đúng được 80% (4/5 câu hỏi), tùy theo nội dung bài viết, một kết quả khá tốt :d ~> điều này cho thấy là Phi3-Mini đã được pretrain khá tốt bằng nguồn dữ liệu wikipedia nên em nó nhớ được thông tin để trả lời :d

Với model Phi3-Mini-3.8B-4bit thì tốc độ nhanh nhưng khả năng suy luận thì còn khá "ngô nghê". Nhưng nếu sử dụng model mistral-7B thì kết quả trả ra sẽ tốt hơn nhiều.

---
title: AutoQuizzer
emoji: 🧑‍🏫
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 4.31.1
app_file: app.py
header: mini
pinned: true
models: [meta-llama/Meta-Llama-3-8B-Instruct]
---

# 🧑‍🏫 AutoQuizzer &nbsp; [![HF Space](https://img.shields.io/badge/%F0%9F%A4%97-Live%20demo-blue.svg)](https://huggingface.co/spaces/deepset/autoquizzer)

Generates a quiz from a URL. You can play the quiz, or let the LLM play it.

Built using: [🏗️ Haystack](https://haystack.deepset.ai/) • 🦙 Llama 3 8B Instruct • ⚡ Groq

<!--- Include in Info tab -->

## How does it work?

![AutoQuizzer](autoquizzer.png)

- **Quiz generation Pipeline**: downloads HTML content from the URL, extracts the text and passes it to Llama 3 to generate a quiz in JSON format.
- You can play the quiz and get a score.
- You can let Llama 3 play the quiz:
  - **closed book answer Pipeline**: the LLM is provided given the general quiz topic and questions. It can answer the questions based on its parametric knowledge and reasoning abilities.
  - **Web RAG answer Pipeline**: for each question, a Google search is performed and the top 3 snippets are included in the prompt for the LLM.

## How to run it locally?

- Clone the repo: `git clone https://github.com/anakin87/autoquizzer`
- Install: `cd autoquizzer && pip install -r requirements.txt`
- Export two environment variables:
  - `GROQ_API_KEY`: API key for the [Groq API](https://groq.com/), used to serve Llama 3.
  - `SERPERDEV_API_KEY`: API key for the [SerperDev API](https://serper.dev/), used to fetch search results.
- Run the webapp: `gradio app.py`

## Customization and potential improvements
- To not exceed the rate limits of Groq's free API, we truncate the text extracted from the URL to 4000 characters. This means that the generated quiz focuses on the beginning of the text. You can increase/remove this limit, taking into account the maximum context length of the model.
- We are using the `OpenAIGenerator` to query Llama 3 on Groq. You can use an OpenAI model with the same generator. You can also use a different generator ([Haystack generators](https://docs.haystack.deepset.ai/docs/generators)).
- In the quiz generation pipeline, we ask the model to generate a JSON. Llama-3-8B-Instruct usually works. You can also create a more robust JSON generation pipeline, as shown in this tutorial: [Generating Structured Output with Loop-Based Auto-Correction](https://haystack.deepset.ai/tutorials/28_structured_output_with_loop).
