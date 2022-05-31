# Changelog

## Current (in progress)

## Version 2.7.1 (2021-05-31)
- Add migration to roolback on resource's schema's name to None
- Upgrade to uData 2.7.1
- Update theme

## Version 2.0.4 (2020-05-04)
- Fix export-csv command (py3 compat)
- Add tutorial videos functionality
- Add functionality geojson preview

## Version 2.0.0 (2020-03-11)
- Migration to Python 3.7
- The new migration system uses a new python based format. Pre-2.0 migrations are not compatible so you might need to upgrade to the latest udata version <2.0.0, execute migrations and then upgrade to udata 2+.
- The targeted mongo version is now Mongo 3.6. Backward support is not guaranteed
- Deprecated celery tasks have been removed, please ensure all old-style tasks (pre 1.6.20) have been consumed before migrating
- New migration system:
  - Use python based migrations instead of relying on mongo internal and deprecated js_exec
  - Handle rollback (optionnal)
  - Detailled history
- Template hooks generalization: allows to dynamically extend template with widgets and snippets from extensions. 
- Markdown now supports

## Version 1.6.20 (2020-01-21)
- New Crowdin translations
- Fix territory routing
- Refactor Celery: py2/py3 compatibility
- Automatically archive dangling harvested datasets :warning: this is enabled
- Refactor celery tasks to avoid models/documents in the transport layer

## Version 1.6.17 (2019-10-28)
- Disallow URLs in first and last names

## Version 1.2.10 (2019-02-15)
- Add testsS

## Version 1.2.9 (2019-01-07)
- Update theme

## Version 1.2.8 (2018-12-01)
- Update x509 public certificate
- Change email recipients
- Inform user if account was deleted.
- Implement SAML Logout request
- Implement initial tests
- Implement Linkchecker

## Version 1.2.7 (2018-11-08)
- Implement harvest settings
- Update theme
- Upgrade to uData 1.6.1
- Update odspt to ods v1.2.1
- Update requirements

## Version 1.2.6 (2018-10-08)
- Improve CKANPT
- Harvester email warnings
- Add dataset harvester source

## Version 1.2.5 (2018-08-09)
- Fix Ckan issue
- Harvester DGT

## Version 1.2.4 (2018-07-10)
- Move home context to theme
- Added os preview and map
- Fix ckanpt issue

## Version 1.2.3 (2018-06-20)
- Small HTML/CSS fix
- Resource preview improve
- Improve resource display and design

## Version 1.2.2 (2018-05-24)
- Upgrade theme to uData 1.3.10
- Territorial configuration
- Resource preview (xlsx and csv)

## Version 1.2.1 (2018-05-10)
- Cache doc pages in redis
- Rework login page
- Rework topic pages
- New Harvest Ods PT
- Rework featured content

## Version 1.1.1 (2018-04-24)
- Added dynamic local docs
- Added new translations
- Adaption to Ckan PT (origin/feature-ckan_pt)

## Version 1.1.0 (2018-04-11)
- Update to Harvest da Justica
- Fixes to authentication module (master)
- Theme v1.1 Added side menu on docs
- Theme v1.1 Improvements in cache and harvester tags
- Open external links in a new tab

## Version 1.0.0 (2018-03-26)
- Theme v1.0
- Fixed issue with migration, preview is used to force migrate
- Removed unused file (origin/feature-migrationHarvest, feature-migrationHarvest)
- Added Old API support (feature-theme1.0)
- Added JSON support for old API
- Added a new harvester for INE . ineDatasets.py cant be changed or removed (feature-harvester_INE)
- Added Harvester do Ambiente
- Minor fixes for GoLive (origin/develop)
- Closing 1.0 sprint

## Version 0.9.0 (2018-03-14)
- Official uData 1.3.0 support
- Theme v0.9 - HTML/CSS changes
- Added contact page
- Fixed dynamic faq pages
- Update translation file (origin/develop)
- Fixed a few issues with importing original files and respective urls

## Version 0.7.0 (2018-02-28)

- Added PT translation, and uData 1.3.x plugin integration
- Fix requirement
- Feature #Theme0.7 - Layout style changed to orange
- Fixed uData 1.3.x plugin entrypoints
- Upgraded card styles to uData 1.3.0.dev
- Added dynamic faqs

## Version 0.5.0 (2018-02-14)

- Initial release