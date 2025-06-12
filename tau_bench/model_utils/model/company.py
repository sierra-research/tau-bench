import os

from .openai import OpenAIModel


class CompanyModel(OpenAIModel):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        base_url = "https://oneai.17usoft.com/v1"
        retrieved_api_key = api_key
        if retrieved_api_key is None:
            retrieved_api_key = os.getenv("COMPANY_API_KEY")

        if retrieved_api_key is None:
            raise ValueError(
                "COMPANY_API_KEY environment variable not set and no api_key provided"
            )

        super().__init__(
            model=model,
            api_key=retrieved_api_key,
            base_url=base_url,
            temperature=temperature,
        )
