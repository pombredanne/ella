from os.path import isfile
import logging.config
import logging
import traceback

from django.utils.itercompat import is_iterable
from django.conf import settings


INSTALLED_APPS_REGISTER = {}


def register(app_name, modules):
    """
    simple module registering for later usage
    we don't want to import admin.py in models.py
    """
    global INSTALLED_APPS_REGISTER
    mod_list = INSTALLED_APPS_REGISTER.get(app_name, [])

    if isinstance(modules, basestring):
        mod_list.append(modules)
    elif is_iterable(modules):
        mod_list.extend(modules)

    INSTALLED_APPS_REGISTER[app_name] = mod_list

def call_modules(auto_discover=()):
    """
    this is called in project urls.py
    for registering desired modules (eg.: admin.py)
    """
    for app in settings.INSTALLED_APPS:
        modules = set(auto_discover)
        if app in INSTALLED_APPS_REGISTER:
            modules.update(INSTALLED_APPS_REGISTER[app])
        for module in modules:
            try:
                imp = '%s.%s' % (app, module)
                mod = __import__(imp, {}, {}, [''])
                inst = getattr(mod, '__install__', lambda:None)
                inst()
            except ImportError, e:
                logging.warning('problem during discovering %s - %s\n%s' % (imp, e, traceback.format_exc()))

def init_logger():
    """init logger with LOGGING_CONFIG_FILE settings option"""
    LOGGING_CONFIG_FILE = getattr(settings, 'LOGGING_CONFIG_FILE', None)
    if isinstance(LOGGING_CONFIG_FILE, basestring) and isfile(LOGGING_CONFIG_FILE):
        logging.config.fileConfig(LOGGING_CONFIG_FILE)

init_logger()
