# gouvpt

Official uData 2.7.1 (Python 3) theme for the Open Data Portal of Portugal

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
apt-get install xmlsec1
```

Generate private/public key:
```bash
openssl req -nodes -new -x509 -keyout saml/private.pem -keyform PEM -out saml/AMA.pem -outform PEM
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
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/develop.pip
```

Ok, you are ready, you can now execute some Development commands.

```bash
udata -?
Available tasks:

  init                Initialize your udata instance (search index, user, etc... )
  generate-fixtures   Build sample fixture data (users, datasets, etc... )
  serve               Runs a development server.
  test                Runs the test suite.
  shell               Run a shell in the app context.

```

Return to udata directory and run:

```bash
./run.sh
```

Run tests with:

```bash
pytest
```
