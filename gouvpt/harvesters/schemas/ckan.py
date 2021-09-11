from voluptuous import (
    Schema, All, Any, Lower, Coerce, DefaultTo, Optional
)
from udata.harvest.filters import (
    boolean, email, to_date, slug, normalize_tag, normalize_string,
    is_url, empty_none, hash
)

RESOURCE_TYPES = ('file', 'file.upload', 'api', 'documentation',
                  'image', 'visualization')


resource = {
    'id': str,
    'position': int,
    'name': All(DefaultTo(''), str),
    'description': All(str, normalize_string),
    'format': All(str, Lower),
    'mimetype': Any(All(str, Lower), None),
    'size': Any(Coerce(int), None),
    'hash': Any(All(str, hash), None),
    'created': All(str, to_date),
    'last_modified': Any(All(str, to_date), None),
    'url': All(str),
    'resource_type': All(empty_none,
                         DefaultTo('file'),
                         str,
                         Any(*RESOURCE_TYPES)
                         ),
}

tag = {
    'id': str,
    Optional('vocabulary_id'): Any(str, None),
    Optional('display_name'): str,
    'name': All(str, normalize_tag),
    Optional('state'): str,
}

organization = {
    'id': str,
    'description': str,
    'created': All(str, to_date),
    'title': str,
    'name': All(str, slug),
    'revision_timestamp': All(str, to_date),
    'is_organization': boolean,
    'state': str,
    'image_url': str,
    'revision_id': str,
    'type': 'organization',
    'approval_status': 'approved'
}

schema = Schema({
    'id': str,
    'name': str,
    'title': str,
    'notes': Any(All(str, normalize_string), None),
    'license_id': All(DefaultTo('not-specified'), str),
    'license_title': Any(str, None),
    'tags': [tag],

    'metadata_created': All(str, to_date),
    'metadata_modified': All(str, to_date),
    'organization': Any(organization, None),
    'resources': [resource],
    'revision_id': str,
    Optional('extras', default=list): [{
        'key': str,
        'value': Any(str, int, float, boolean, dict, list),
    }],
    'private': boolean,
    'type': 'dataset',
    'author': Any(str, None),
    'author_email': All(empty_none, Any(All(str, email), None)),
    'maintainer': Any(str, None),
    'maintainer_email': All(empty_none, Any(All(str, email), None)),
    'state': Any(str, None),
}, required=True, extra=True)
