## 

A pipeline using DeepSeek to extract phytochemical data from literature sources.

## Installation

Install requires requires wcvpy>=1.3.2, to install see https://github.com/alrichardbollans/wcvpy

and `phytochempy`, see https://github.com/alrichardbollans/phytochempy

then to install, run:

`pip install git+https://github.com/alrichardbollans/phytochemMiner`


## Usage Example

```python
from phytochemMiner import get_phytochem_model, run_phytochem_model

model, limit = get_phytochem_model(dotenv_path='.env')
fulltextpath = 'path_to_txt_file.txt'
run_phytochem_model(model, fulltextpath,
                    limit,
                    json_dump='output_json_file.json')

```

### Manual verification

Outputs from this process (the `json_dump` files) can be manually verified using our reference verifier shiny app, hosted here: https://huggingface.co/spaces/alrichardbollans/PhytochemReferenceVerifier


### References & Acknowledgements
Petr Knoth et al., ‘CORE: A Global Aggregation Service for Open Access Papers’, Scientific Data 10, no. 1 (2023): 366, https://doi.org/10.1038/s41597-023-02208-w.

Denny Vrandečić and Markus Krötzsch, ‘Wikidata: A Free Collaborative Knowledgebase’, Communications of the ACM 57, no. 10 (2014): 78–85.

Farit Mochamad Afendi, Taketo Okada,, Mami Yamazaki, Aki-Hirai-Morita, Yukiko Nakamura,
Kensuke Nakamura, Shun Ikeda, Hiroki Takahashi, Md. Altaf-Ul-Amin, Latifah, Darusman, Kazuki
Saito, Shigehiko Kanaya, “KNApSAcK Family Databases: Integrated Metabolite-Plant Species
Databases for Multifaceted Plant Research,” Plant Cell Physiol., 53, e1(1-12), (2012). doi:
10.1093/pcp/pcr165.

The developers acknowledge Research Computing at the James Hutton Institute for providing computational resources and technical support for the 'UK’s
Crop Diversity Bioinformatics HPC' (BBSRC grants BB/S019669/1 and BB/X019683/1), use of which has contributed to the development of the model used in
this analysis.
