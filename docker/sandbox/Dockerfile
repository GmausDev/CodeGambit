FROM python:3.12-slim
RUN useradd -m -s /bin/bash sandbox
RUN pip install --no-cache-dir langchain-core langchain-community langchain-openai pydantic pytest numpy
WORKDIR /sandbox
USER sandbox
CMD ["python3"]
