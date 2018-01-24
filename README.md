# gouvpt

Official udata theme for the Open Data Portal of Portugal

## Usage

Install the theme package in you udata environement:

```bash
git clone https://github.com/amagovpt/gouvpt.git
pip install gouvpt/
```

Then, define the installed theme as current in you `udata.cfg`:

```python
PLUGINS = ['auth_gouvpt']
THEME = 'gouvpt'
```

### configuration parameters

Some features are optionnal and can be enabled with the following `udata.cfg` parameters

- `gouvpt_GOVBAR = True/False`: Toggle the govbar

Portuguese portal provides authentication with SmartId Card and Autenticacao.gov.pt
Set your `udata.cfg` with the following parameters

- `SECURITY_SAML_ENTITY_ID = 'www.dadosabertos.gov.pt'` : Entity ID
- `SECURITY_SAML_ENTITY_NAME = 'DadosAbertosUdata'` : Entity Name
- `SECURITY_SAML_KEY_FILE = '...path.../private.pem'` : Private Entity key PEM file path
- `SECURITY_SAML_CERT_FILE = '...path.../AMA.pem'` : Public Entity Certificate PEM file path
- `SECURITY_SAML_IDP_METADATA = 'metadata_file1.xml,metadata_file2.xml,....'` : Metadata files path for IDP's
- `SECURITY_SAML_FAAALEVEL = 1` : : Authentication Level requested to autenticacao.gov.pt

See autenticacao.gov.pt and SAML2 protocol docs for extra information

## Development

### Local setup

If you want to execute some development tasks like extracting the translations or running the test suite, you need to install the dependencies localy (in a virtualenv).

```bash
virtualenv --python=python2.7 venv 
source venv/bin/activate
pip install -r requirements/develop.pip
```

If you want to build assets, you also need node.js. The prefered way is with [nvm][]:

```bash
nvm use
npm install
inv assets_build
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
inv serve
```