import json
import os

import langchain_core
import pandas as pd
import pydantic_core

from phytochemMiner import read_file_and_chunk, standard_prompt, TaxaData, \
    deduplicate_and_standardise_output_taxa_lists, get_txt_from_file, filter_classes
from phytochemMiner import add_inchi_keys, add_all_extra_info_to_output


def run_phytochem_model(model, text_file: str, context_window: int, wcvp: pd.DataFrame, remove_classes: bool = False, json_dump: str = None,
                        single_chunk: bool = True, rerun=True, rerun_inchi_resolution: bool = True) -> TaxaData:
    """
    Run the given LLM to process a given text file and extract structured taxonomical data.

    This function processes a text file using the specified model, extracts structured output, deduplicates
    the extracted data, and optionally filters and adds extra information to the output. The processing may
    include additional steps such as chunking the text and managing concurrency to adhere to constraints on
    the model's usage. Optionally, the results can be saved and loaded from a JSON file to avoid redundant
    processing. Additional configurations allow rerunning specific steps and resolving InChI keys.

    :param model: The model used for extracting structured taxonomical data.
    :param text_file: The file path of the input text to be processed.
    :type text_file: str
    :param context_window: The context window size for chunking the input text.
    :type context_window: int
    :param wcvp: DataFrame containing the WCVP (World Checklist of Vascular Plants) for reference.
    :type wcvp: pd.DataFrame
    :param remove_classes: A boolean indicating whether to exclude compound classes (default: False).
    :type remove_classes: bool, optional
    :param json_dump: Path to a JSON file for saving/loading processed data. If the file exists and rerun
        is False, the output is loaded from this file (default: None).
    :type json_dump: str, optional
    :param single_chunk: Whether to process the text in a single chunk. If False, chunking logic is applied
        for further splitting and processing (default: True).
    :type single_chunk: bool, optional
    :param rerun: If False and the JSON dump exists, the function avoids redundant processing and instead
        loads the output from the JSON file (default: True).
    :type rerun: bool, optional
    :param rerun_inchi_resolution: If True, reruns InChI resolution for resolving keys and updates
        the JSON file (default: True).
    :rtype: TaxaData
    """
    if not rerun and os.path.exists(json_dump):
        with open(json_dump, "r") as file_:
            json_dict = json.load(file_)
            output = TaxaData.model_validate(json_dict)
        if rerun_inchi_resolution:
            add_inchi_keys(output)
            with open(json_dump, "w") as file_:
                json_out = output.model_dump(mode="json")
                json.dump(json_out, file_)
        return output

    if not single_chunk:
        raise NotImplementedError
    text_chunks = read_file_and_chunk(text_file, context_window)
    if single_chunk:
        # For most of analysis, will be testing on single chunks as this is how we've annotated them.
        # In this instance, the chunks should fit in the context window
        if not len(text_chunks) == 1:
            print(f'splitting chunks for {text_file}')
    # A few different methods, depending on the specific model are used to get a structured output
    # and this is handled by with_structured_output. See https://python.langchain.com/docs/how_to/structured_output/
    extractor = standard_prompt | model.with_structured_output(schema=TaxaData, include_raw=False)
    try:

        extractions = extractor.batch(
            [{"text": text} for text in text_chunks],
            {"max_concurrency": 1},
            # limit the concurrency by passing max concurrency! Otherwise Requests rate limit exceeded
        )
    except (langchain_core.exceptions.OutputParserException, pydantic_core._pydantic_core.ValidationError) as e:
        raise NotImplementedError
        # When there is too much info extracted the extractor can't parse the output json, so make chunks smaller.
        # This can also happen because of limits on model max output tokens
        print(f'Warning: reducing size of chunk as output json is too large to parse. For file {text_file}')

        new_chunks = split_text_chunks(text_chunks)
        print(f'Length of old chunk: {len(text_chunks[0])}')

        extractions = []
        for text in new_chunks:
            try:
                chunk_output = extractor.invoke({"text": text})
                extractions.append(chunk_output)
            except Exception as e:
                more_chunks = split_text_chunks([text])
                for more_text in more_chunks:
                    try:
                        chunk_output = extractor.invoke({"text": more_text})
                        extractions.append(chunk_output)
                    except Exception as e:
                        # print(f'Unknown error "{e}" for text with length {len(more_text)}: {more_text}')
                        even_more_chunks = split_text_chunks([more_text])
                        for even_more_text in even_more_chunks:
                            try:
                                chunk_output = extractor.invoke({"text": even_more_text})
                                extractions.append(chunk_output)
                            except Exception as e:
                                print(
                                    f'Unknown error "{e}" for text with length {len(even_more_text)}: {even_more_text}')

    output = []

    for extraction in extractions:
        if extraction is not None:
            if extraction.taxa is not None:
                output.extend(extraction.taxa)

    deduplicated_extractions = deduplicate_and_standardise_output_taxa_lists(output)
    if remove_classes:
        filter_classes(deduplicated_extractions)
    add_all_extra_info_to_output(deduplicated_extractions, wcvp)

    text = get_txt_from_file(text_file)
    deduplicated_extractions.text = text

    if json_dump:
        with open(json_dump, "w") as file_:
            json_out = deduplicated_extractions.model_dump(mode="json")
            json.dump(json_out, file_)

    return deduplicated_extractions


def get_input_size_limit(total_context_window_k: int):
    # Output tokens so far is a tiny fraction, so allow 5% of context window for output
    out_units = total_context_window_k * 1000
    input_size = int(out_units * 0.95)
    return input_size


def get_phytochem_model(apikey: str = None, dotenv_path=None):
    """
    Gets an instance of the DeepSeek model configured with the specified parameters.

    The function provides an instance of the ChatDeepSeek model, either using the provided
    API key or loading it from an environment file. It specifies a default model type
    'deepseek-chat' with a predefined hyperparameter set for configuration.

    Parameters:
    apikey: str, optional
        The API key to authenticate with DeepSeek. If None, it retrieves the key from the
        environment file.
    dotenv_path: str, optional
        The file path to a `.env` file containing environment variables, including the API
        key under DEEPSEEK_API_KEY=. Defaults to None.

    Returns:
    tuple
        A tuple consisting of the configured DeepSeek model instance and the input size
        limit for the model.
    """

    # DeepSeek V3
    # Created 30/12/2024
    # Max tokens 128k
    # Input/Output: $0.28/0.42/1M tokens
    # https://api-docs.deepseek.com/quick_start/pricing/

    # DeepSeek-R1, specified via model="deepseek-reasoner", does not support tool calling or structured output.
    # Those features are supported by DeepSeek-V3 (specified via model="deepseek-chat").

    from langchain_deepseek import ChatDeepSeek
    hparams = {'temperature': 0}

    if apikey is None:
        # Get API keys
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=dotenv_path)

        model = ChatDeepSeek(
            model="deepseek-chat", **hparams)
    else:
        model = ChatDeepSeek(
            model="deepseek-chat", api_key=apikey, **hparams)
    return model, get_input_size_limit(128)
