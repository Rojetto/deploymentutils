# deploymentutils

This repo contains a small python package to facilitate deployment of some personal projects.


## Overview

This package provides a thin layer on top of [fabric](https://www.fabfile.org/) to execute commands with a state like
- current working directory
- activated virtual environment (not yet implemented)

It also tries to simplify to deploy/maintain multiple instances of the same software but with varying fixtures, including one or more local instances for testing.

## Motivation

The package is mainly intended to facilitate deployment tasks (e.g. for django apps) by running a simple python script.
Compared to configuration management tools like *Ansible* this approach is far less powerful and scalable.
However, it might be easier to understand for developers and thus lowering the hurdle to deploy applications by them selves.

## Assumed Directory Layout

The scripts marked with [*] make use of this module.

    <general project dir>
    │
    │
    ├── project-src-repo/                       ← official project repo
    │   ├── .git/
    │   ├── deployment/
    │   │   ├── some_files/
    │   │   ├── deploy.py      [*]              ← original deployment script  (delivered by the project)
    │   │   └── ...
    │   ├── django_project/
    │   │   ├── settings.py
    │   │   └── ...
    │   ├── django_app/
    │   │   ├── views.py
    │   │   └── ...
    │   ├── manage.py
    │   └── ...
    │
    ├── instance-specific/
    │   ├── README.md
    │   ├── demo
    │   │   ├── .git/
    │   │   ├── deploy.py
    │   │   ├── project_data
    │   │   └── ...
    │   ├── production
    │   │   ├── .git/
    │   │   ├── deploy.py      [*]
    │   │   ├── project_data
    │   │   └── ...
    │   ├── testing
    │   │   ├── .git/
    │   │   ├── deploy.py      [*]
    │   │   ├── project_data
    │   │   └── ...
    │   └── ...
    │
    ├── local_testing/               ← contents of this directory are autogenerated
    │   ├── deploy.py          [*]
    │   ├── <appname>_deployment
    │   └── ...
    .



## Status

Still under development and not comprehensively tested.


## Known Issues

- If a command started by `c.run("some_command")` is reading input, then the calling python process waits 'forever', i.e. until interrupted manually.
    - possible solution fragment: https://stackoverflow.com/questions/35751295/python-subprocess-check-to-see-if-the-executed-script-is-asking-for-user-input
