import os
import re

blacklist_extensions = ('.txt', '.md', '.man', '.lang', '.loc', '.tex', '.texi', '.rst',
                        '.gif', '.png', '.jpg', '.jpeg', '.svg', '.ico',
                        '.css', '.scss', '.less',
                        '.gradle', '.cmake', '.lock', '.ini', 
                        '.out', '.class',
                        '.tar', '.gz', '.zip',
                        '.pdf')
blacklist_path = '|'.join([
    r'^.*/\.github.*',
    r'^.*/changelog.*',
    r'^.*/test(s)?.*',
    r'^.*/docs.*',
    r'^.*/node_modules.*',
])
blacklist_names = r"^(install|changelog(s)?|change(s)?|author(s)?|news|readme|todo|about(s)?|credit(s)?|license|thank(s)?|release(s)?|release(s)?|release(_|-)note(s)?|version(s)?|makefile|mvnw|gradlew|gemfile)$"
blacklist_files = r"^(|\.git|\.gitignore|\.travis|\.classpath|\.project|pom\.xml|gradle-wrapper\.properties|strings\.xml|arrays\.xml)$"


def is_invalid_extension(filepath):
    extension = os.path.splitext(filepath)[1]
    return extension in blacklist_extensions


def is_invalid_path(filepath):
    return re.match(blacklist_path, filepath, re.IGNORECASE)


def is_invalid_name(filepath):
    name = os.path.splitext(filepath)[0]
    return re.match(blacklist_names, name, re.IGNORECASE)


def is_invalid_file(filepath):
    file = os.path.basename(os.path.normpath(filepath))
    return re.match(blacklist_files, file, re.IGNORECASE)

def is_blacklisted(filepath):
    return is_invalid_extension(filepath) or is_invalid_path(filepath) or is_invalid_name(filepath) or is_invalid_file(filepath)
