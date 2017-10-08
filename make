#!/usr/bin/env python3.6
import logging
import os
import shlex
import shutil
import subprocess
import sys

try:
    import docker
    import jinja2
    from clinner.command import command, Type as CommandType
    from clinner.run import Main
except ImportError:
    import importlib
    import pip
    import site

    print('Installing dependencies')
    pip.main(['install', '--user', '-qq', 'clinner', 'docker', 'jinja2'])

    importlib.reload(site)

    import docker
    import jinja2
    from clinner.command import command, Type as CommandType
    from clinner.run import Main

logger = logging.getLogger('cli')

docker_cli = docker.from_env()


@command(command_type=CommandType.SHELL,
         args=((('--name',), {'help': 'Docker image name', 'default': 'barrenero-telegram'}),
               (('--tag',), {'help': 'Docker image tag', 'default': 'latest'})),
         parser_opts={'help': 'Docker build for local environment'})
def build(*args, **kwargs):
    tag = '{name}:{tag}'.format(**kwargs)

    cmd = shlex.split('docker build -t {} .'.format(tag)) + list(args)

    return [cmd]


def _volumes(code=False):
    volumes = [
        '{}:/srv/apps/barrenero-telegram/logs'.format(os.path.join("/var/log/barrenero", "telegram")),
        '{}:/srv/apps/barrenero-telegram/.data'.format(os.path.join(os.getcwd(), ".data")),
    ]

    if code:
        volumes.append('-v {}:/srv/apps/barrenero-telegram'.format(os.getcwd()))

    return volumes


def _create_network(name):
    if not docker_cli.networks.list(names=name):
        docker_cli.networks.create(name)


@command(command_type=CommandType.PYTHON,
         args=((('-n', '--name',), {'help': 'Docker image name', 'default': 'barrenero-telegram'}),
               (('--network',), {'help': 'Docker network', 'default': 'barrenero'}),
               (('-c', '--code',), {'help': 'Add code folder as volume', 'action': 'store_true'}),
               (('-i', '--interactive'), {'help': 'Docker image tag', 'action': 'store_true'})),
         parser_opts={'help': 'Run application'})
def run(*args, **kwargs):
    _create_network(kwargs['network'])
    try:
        docker_cli.containers.run(
            image='barrenero-telegram:latest',
            command=shlex.split('-q --skip-check run') + list(args),
            detach=not kwargs['interactive'],
            name=kwargs['name'],
            network=kwargs['network'],
            auto_remove=True,
            volumes=_volumes(kwargs['code']),
        )
    except KeyboardInterrupt:
        docker_cli.containers.get(kwargs['name']).stop()


@command(command_type=CommandType.PYTHON,
         args=((('-n', '--name',), {'help': 'Docker image name', 'default': 'barrenero-telegram'}),
               (('--network',), {'help': 'Docker network', 'default': 'barrenero'}),
               (('-c', '--code',), {'help': 'Add code folder as volume', 'action': 'store_true'})),
         parser_opts={'help': 'Run application'})
def create(*args, **kwargs):
    _create_network(kwargs['network'])
    docker_cli.containers.create(
        image='barrenero-telegram:latest',
        command=shlex.split('-q run') + list(args),
        name=kwargs['name'],
        network=kwargs['network'],
        auto_remove=True,
        volumes=_volumes(kwargs['code']),
    )


@command(command_type=CommandType.PYTHON,
         args=((('--path',), {'help': 'Barrenero full path', 'default': '/usr/local/lib/barrenero'}),
               (('bot_token',), {'help': 'Telegram bot token'}),),
         parser_opts={'help': 'Install the application in the system'})
def install(*args, **kwargs):
    if not os.geteuid() == 0:
        logger.error('Script must be run as root')
        return -1

    path = os.path.abspath(os.path.join(kwargs['path'], 'barrenero-telegram'))

    # Jinja2 builder
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(path, 'templates')))
    systemd_j2_context = {
        'app': {
            'name': 'barrenero-telegram',
            'path': path,
        },
        'telegram': {
            'token': kwargs['bot_token'],
        }
    }

    # Create app directory
    logger.info("[Barrenero Telegram] Install app under %s", path)
    shutil.rmtree(path, ignore_errors=True)
    shutil.copytree('.', path)

    # Create setup file
    logger.info("[Barrenero Telegram] Defining config file using token %s", kwargs['bot_token'])
    with open(os.path.join(path, 'setup.cfg'), 'w') as f:
        f.write(j2_env.get_template('setup.cfg.jinja2').render(systemd_j2_context))

    # Create Systemd unit
    logger.info("[Barrenero Telegram] Create Systemd unit and enable it")
    with open('/etc/systemd/system/barrenero_telegram.service', 'w') as f:
        f.write(j2_env.get_template('barrenero_telegram.service.jinja2').render(systemd_j2_context))
    subprocess.run(shlex.split('systemctl enable barrenero_telegram.service'))
    subprocess.run(shlex.split('systemctl daemon-reload'))

    logger.info("[Barrenero Telegram] Installation completed")


if __name__ == '__main__':
    sys.exit(Main().run())
