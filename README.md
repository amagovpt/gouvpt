# gouvpt

Official uData 1.6.11 theme for the Open Data Portal of Portugal

## Usage

Clone and install the theme package in your udata environment:

```bash
git clone https://github.com/amagovpt/gouvpt.git
pip install gouvpt/
```

Then, define the installed theme as current in you `udata.cfg`:

```python
PLUGINS = ['gouvpt_saml','gouvpt_faqs']
THEME = 'gouvpt'
DEFAULT_LANGUAGE = 'pt'
```

### Portuguese Smart Card Authentication

Portuguese uData portal provides authentication with SmartIdCards and Autenticacao.gov.pt

Install dependencies: 

```bash
apt-get install xmlsec1-openssl
```

Set your `udata.cfg` with the following parameters

- `SECURITY_SAML_ENTITY_ID = 'www.dadosabertos.gov.pt'` : Entity ID
- `SECURITY_SAML_ENTITY_NAME = 'DadosAbertosUdata'` : Entity Name
- `SECURITY_SAML_KEY_FILE = '...path.../private.pem'` : Private Entity key PEM file path
- `SECURITY_SAML_CERT_FILE = '...path.../AMA.pem'` : Public Entity Certificate PEM file path
- `SECURITY_SAML_IDP_METADATA = 'metadata_file1.xml,metadata_file2.xml,..'` : Metadata files for IDP's
- `SECURITY_SAML_FAAALEVEL = 1` : : Authentication Level requested to autenticacao.gov.pt

See autenticacao.gov.pt and SAML2 protocol docs for feature information.

## Development

### Local setup

If you want to execute some development tasks like extracting the translations or running the test suite, you need to install the dependencies localy (in a virtualenv).

```bash
virtualenv --python=python2.7 venv 
source venv/bin/activate
pip install -r requirements/develop.pip
```

Ok, you are ready, you can now execute some Development commands.

```bash
inv -l
Available tasks:

  all            Run tests, reports and packaging
  assets-build   Build static assets
  assets-watch   Build assets on change
  clean          Cleanup all build artifacts
  cover          Run tests suite with coverage
  dist           Package for distribution
  i18n           Extract translatable strings
  i18nc          Compile translations
  pydist         Perform python packaging (without compiling assets)
  qa             Run a quality report
  test           Run tests suite
```

Return to udata directory and run:

```bash
udata serve
```

Run tests with:

```bash
pytest
```
