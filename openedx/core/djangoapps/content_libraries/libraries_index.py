""" Code to allow indexing content libraries """

import logging
from abc import ABC, abstractmethod

from django.conf import settings
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError
from search.elastic import ElasticSearchEngine, _translate_hits, _process_field_filters, RESERVED_CHARACTERS
from search.search_engine_base import SearchEngine
from opaque_keys.edx.locator import LibraryUsageLocatorV2

from openedx.core.djangoapps.content_libraries.signals import (
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_UPDATED,
    CONTENT_LIBRARY_DELETED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_UPDATED,
    LIBRARY_BLOCK_DELETED,
)
from openedx.core.djangoapps.content_libraries.library_bundle import LibraryBundle
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.lib.blockstore_api import get_bundle

log = logging.getLogger(__name__)

MAX_SIZE = 10000  # 10000 is the maximum records elastic is able to return in a single result. Defaults to 10.


class SearchIndexerBase(ABC):
    INDEX_NAME = None
    DOCUMENT_TYPE = None
    ENABLE_INDEXING_KEY = None

    @classmethod
    @abstractmethod
    def get_item_definition(cls, item):
        """
        Returns a serializable dictionary which can be stored in elasticsearch.
        """

    @classmethod
    def index_items(cls, items):
        """
        Index the specified libraries. If they already exist, replace them with new ones.
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        items = [cls.get_item_definition(item) for item in items]
        return searcher.index(cls.DOCUMENT_TYPE, items)

    @classmethod
    def get_items(cls, ids=None, filter_terms=None, text_search=None):
        """
        Retrieve a list of items from the index.
        Arguments:
            ids - List of ids to be searched for in the index
            filter_terms - Dictionary of filters to be applied
            text_search - String which is used to do a text search in the supported indexes.
        """
        if filter_terms is None:
            filter_terms = {}
        if ids is not None:
            filter_terms = {
                "id": [str(item) for item in ids],
                **filter_terms
            }

        if text_search:
            response = cls._perform_elastic_search(filter_terms, text_search)
        else:
            searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
            response = searcher.search(doc_type=cls.DOCUMENT_TYPE, field_dictionary=filter_terms, size=MAX_SIZE)

        response = [result["data"] for result in response["results"]]
        return sorted(response, key=lambda i: i["id"])

    @classmethod
    def remove_items(cls, ids):
        """
        Remove the provided ids from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        ids_str = [str(i) for i in ids]
        searcher.remove(cls.DOCUMENT_TYPE, ids_str)

    @classmethod
    def remove_all_items(cls):
        """
        Remove all items from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        response = searcher.search(doc_type=cls.DOCUMENT_TYPE, filter_dictionary={}, size=MAX_SIZE)
        ids = [result["data"]["id"] for result in response["results"]]
        searcher.remove(cls.DOCUMENT_TYPE, ids)

    @classmethod
    def indexing_is_enabled(cls):
        """
        Checks to see if the indexing feature is enabled
        """
        return settings.FEATURES.get(cls.ENABLE_INDEXING_KEY, False)

    @classmethod
    def _perform_elastic_search(cls, filter_terms, text_search):
        """
        Build a query and search directly on elasticsearch
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        return _translate_hits(searcher._es.search(
            doc_type=cls.DOCUMENT_TYPE,
            index=searcher.index_name,
            body=cls.build_elastic_query(filter_terms, text_search),
            size=MAX_SIZE
        ))

    @staticmethod
    def build_elastic_query(filter_terms, text_search):
        """
        Build and return an elastic query for doing text search on a library
        """
        # Remove reserved characters (and ") from the text to prevent unexpected errors.
        text_search_normalised = text_search.translate(text_search.maketrans('', '', RESERVED_CHARACTERS + '"'))
        # Wrap with asterix to enable partial matches
        text_search_normalised = "*{}*".format(text_search_normalised)
        terms = [
            {
                'terms': {
                    item: filter_terms[item]
                }
            }
            for item in filter_terms
        ]
        return {
            'query': {
                'filtered': {
                    'query': {
                        'bool': {
                            'should': [
                                {
                                    'query_string': {
                                        'query': text_search_normalised,
                                        "fields": ["content.*"],
                                        "minimum_should_match": "100%",
                                    },
                                },
                                # Add a special wildcard search for id, as it contains a ":" character which is filtered out
                                # in query_string
                                {
                                    'wildcard': {
                                        'id': {
                                            'value': '*{}*'.format(text_search),
                                        }
                                    },
                                },
                            ],
                        },
                    },
                    'filter': {
                        'bool': {
                            'must': terms
                        }
                    }
                },
            },
        }


class ContentLibraryIndexer(SearchIndexerBase):
    """
    Class to perform indexing for blockstore-based content libraries
    """

    INDEX_NAME = "content_library_index"
    ENABLE_INDEXING_KEY = "ENABLE_CONTENT_LIBRARY_INDEX"
    DOCUMENT_TYPE = "content_library"

    @classmethod
    def get_item_definition(cls, library_key):
        from openedx.core.djangoapps.content_libraries.api import DRAFT_NAME

        ref = ContentLibrary.objects.get_by_key(library_key)
        lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
        num_blocks = len(lib_bundle.get_top_level_usages())
        last_published = lib_bundle.get_last_published_time()
        last_published_str = None
        if last_published:
            last_published_str = last_published.strftime('%Y-%m-%dT%H:%M:%SZ')
        (has_unpublished_changes, has_unpublished_deletes) = lib_bundle.has_changes()

        bundle_metadata = get_bundle(ref.bundle_uuid)

        return {
            "id": str(library_key),
            "uuid": str(bundle_metadata.uuid),
            "title": bundle_metadata.title,
            "description": bundle_metadata.description,
            "num_blocks": num_blocks,
            "version": bundle_metadata.latest_version,
            "last_published": last_published_str,
            "has_unpublished_changes": has_unpublished_changes,
            "has_unpublished_deletes": has_unpublished_deletes,
            # only 'content' field is analyzed by elastisearch, and allows text-search
            "content": {
                "id": str(library_key),
                "title": bundle_metadata.title,
                "description": bundle_metadata.description,
            },
        }


class LibraryBlockIndexer(SearchIndexerBase):
    """
    Class to perform indexing on the XBlocks in content libraries.
    """

    INDEX_NAME = "content_library_index"
    ENABLE_INDEXING_KEY = "ENABLE_CONTENT_LIBRARY_INDEX"
    DOCUMENT_TYPE = "content_library_block"

    @classmethod
    def get_item_definition(cls, usage_key):
        from openedx.core.djangoapps.content_libraries.api import get_block_display_name, _lookup_usage_key

        def_key, lib_bundle = _lookup_usage_key(usage_key)
        is_child = usage_key in lib_bundle.get_bundle_includes().keys()
        return {
            "id": str(usage_key),
            "library_key": str(lib_bundle.library_key),
            "is_child": is_child,
            "def_key": str(def_key),
            "display_name": get_block_display_name(def_key),
            "block_type": def_key.block_type,
            "has_unpublished_changes": lib_bundle.does_definition_have_unpublished_changes(def_key),
            # only 'content' field is analyzed by elastisearch, and allows text-search
            "content": {
                "id": str(usage_key),
                "display_name": get_block_display_name(def_key),
            },
        }


@receiver(CONTENT_LIBRARY_CREATED)
@receiver(CONTENT_LIBRARY_UPDATED)
@receiver(LIBRARY_BLOCK_CREATED)
@receiver(LIBRARY_BLOCK_UPDATED)
@receiver(LIBRARY_BLOCK_DELETED)
def index_library(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Index library when created or updated, or when its blocks are modified.
    """
    if ContentLibraryIndexer.indexing_is_enabled():
        try:
            ContentLibraryIndexer.index_items([library_key])
            if kwargs.get('update_blocks', False):
                blocks = LibraryBlockIndexer.get_items(filter_terms={
                    'library_key': str(library_key)
                })
                usage_keys = [LibraryUsageLocatorV2.from_string(block['id']) for block in blocks]
                LibraryBlockIndexer.index_items(usage_keys)
        except ConnectionError as e:
            log.exception(e)


@receiver(CONTENT_LIBRARY_DELETED)
def remove_library_index(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Remove from index when library is deleted
    """
    if ContentLibraryIndexer.indexing_is_enabled():
        try:
            ContentLibraryIndexer.remove_items([library_key])
            blocks = LibraryBlockIndexer.get_items(filter_terms={
                'library_key': str(library_key)
            })
            LibraryBlockIndexer.remove_items([block['id'] for block in blocks])
        except ConnectionError as e:
            log.exception(e)


@receiver(LIBRARY_BLOCK_CREATED)
@receiver(LIBRARY_BLOCK_UPDATED)
def index_block(sender, usage_key, **kwargs):  # pylint: disable=unused-argument
    """
    Index block metadata when created
    """
    if LibraryBlockIndexer.indexing_is_enabled():
        try:
            LibraryBlockIndexer.index_items([usage_key])
        except ConnectionError as e:
            log.exception(e)


@receiver(LIBRARY_BLOCK_DELETED)
def remove_block_index(sender, usage_key, **kwargs):  # pylint: disable=unused-argument
    """
    Remove the block from the index when deleted
    """
    if LibraryBlockIndexer.indexing_is_enabled():
        try:
            LibraryBlockIndexer.remove_items([usage_key])
        except ConnectionError as e:
            log.exception(e)
