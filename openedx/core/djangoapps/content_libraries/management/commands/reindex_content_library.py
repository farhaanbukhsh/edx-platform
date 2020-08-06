""" Management command to update content libraries' search index """


from textwrap import dedent

from cms.djangoapps.contentstore.management.commands.prompt import query_yes_no

from django.core.management import BaseCommand
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx.core.djangoapps.content_libraries.api import DRAFT_NAME
from openedx.core.djangoapps.content_libraries.libraries_index import ContentLibraryIndexer, LibraryBlockIndexer
from openedx.core.djangoapps.content_libraries.library_bundle import LibraryBundle
from openedx.core.djangoapps.content_libraries.models import ContentLibrary


class Command(BaseCommand):
    """
    Command to reindex blockstore-based content libraries (single, multiple or all available)

    Examples:

        ./manage.py reindex_content_library lib1 lib2 - reindexes libraries with keys lib1 and lib2
        ./manage.py reindex_content_library --all - reindexes all available libraries
        ./manage.py reindex_content_library --clear-all - clear all libraries indexes
    """
    help = dedent(__doc__)
    CONFIRMATION_PROMPT_CLEAR = u"This will clear all indexed libraries from elasticsearch. Do you want to continue?"
    CONFIRMATION_PROMPT_ALL = u"Reindexing all libraries might be a time consuming operation. Do you want to continue?"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-all',
            action='store_true',
            dest='clear-all',
            help='Clear all library indexes'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='Reindex all libraries'
        )
        parser.add_argument('library_ids', nargs='*')

    def handle(self, *args, **options):
        if options['clear-all']:
            if query_yes_no(self.CONFIRMATION_PROMPT_CLEAR, default="no"):
                ContentLibraryIndexer.remove_all_items()
                LibraryBlockIndexer.remove_all_items()
            return

        if options['all']:
            if query_yes_no(self.CONFIRMATION_PROMPT_ALL, default="no"):
                library_keys = [library.library_key for library in ContentLibrary.objects.all()]
            else:
                return
        else:
            library_keys = list(map(LibraryLocatorV2.from_string, options['library_ids']))

        ContentLibraryIndexer.index_items(library_keys)

        for library_key in library_keys:
            ref = ContentLibrary.objects.get_by_key(library_key)
            lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
            LibraryBlockIndexer.index_items(lib_bundle.get_all_usages())
