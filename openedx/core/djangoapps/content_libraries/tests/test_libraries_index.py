"""
Testing indexing of blockstore based content libraries
"""

from django.test.utils import override_settings
from search.search_engine_base import SearchEngine
from opaque_keys.edx.locator import LibraryLocatorV2

from openedx.core.djangoapps.content_libraries.libraries_index import ContentLibraryIndexer, LibraryNotIndexedException
from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest


class ContentLibraryIndexerIndexer(ContentLibrariesRestApiTest):
    """
    Tests the operation of ContentLibraryIndexer
    """

    def setUp(self):
        super().setUp()
        ContentLibraryIndexer.remove_all_libraries()
        self.searcher = SearchEngine.get_search_engine(ContentLibraryIndexer.INDEX_NAME)

    @override_settings(SEARCH_ENGINE="search.tests.mock_search_engine.MockSearchEngine")
    def test_index_libraries(self):
        """
        Test if libraries are being indexed correctly
        """
        result1 = self._create_library(slug="test-lib-index-1", title="Title 1", description="Description")
        library_key1 = LibraryLocatorV2.from_string(result1['id'])

        result2 = self._create_library(slug="test-lib-index-2", title="Title 2", description="Description")
        library_key2 = LibraryLocatorV2.from_string(result2['id'])

        response = self.searcher.search(doc_type=ContentLibraryIndexer.LIBRARY_DOCUMENT_TYPE, filter_dictionary={})
        self.assertEqual(response['total'], 2)

        for result in [result1, result2]:
            library_key = LibraryLocatorV2.from_string(result['id'])
            response = ContentLibraryIndexer.get_libraries([library_key])[0]

            self.assertEqual(response['id'], result['id'])
            self.assertEqual(response['title'], result['title'])
            self.assertEqual(response['description'], result['description'])
            self.assertEqual(response['uuid'], result['bundle_uuid'])
            self.assertEqual(response['num_blocks'], 0)
            self.assertEqual(response['version'], result['version'])
            self.assertEqual(response['last_published'], None)
            self.assertEqual(response['has_unpublished_changes'], False)
            self.assertEqual(response['has_unpublished_deletes'], False)

    @override_settings(SEARCH_ENGINE="search.tests.mock_search_engine.MockSearchEngine")
    def test_remove_all_libraries(self):
        """
        Test if remove_all_libraries() deletes all libraries
        """
        result1 = self._create_library(slug="test-lib-rm-all-1", title="Title 1", description="Description")
        library_key1 = LibraryLocatorV2.from_string(result1['id'])
        result2 = self._create_library(slug="test-lib-rm-all-2", title="Title 2", description="Description")
        library_key2 = LibraryLocatorV2.from_string(result2['id'])

        response = self.searcher.search(doc_type=ContentLibraryIndexer.LIBRARY_DOCUMENT_TYPE, filter_dictionary={})
        self.assertEqual(response['total'], 2)

        ContentLibraryIndexer.remove_all_libraries()
        response = self.searcher.search(doc_type=ContentLibraryIndexer.LIBRARY_DOCUMENT_TYPE, filter_dictionary={})
        self.assertEqual(response['total'], 0)

    @override_settings(SEARCH_ENGINE="search.tests.mock_search_engine.MockSearchEngine")
    def test_update_libraries(self):
        """
        Test if indexes are updated when libraries are updated
        """
        lib = self._create_library(slug="test-lib-update", title="Title", description="Description")
        library_key = LibraryLocatorV2.from_string(lib['id'])

        self._update_library(lib['id'], title="New Title", description="New Title")

        response = ContentLibraryIndexer.get_libraries([library_key])[0]

        self.assertEqual(response['id'], lib['id'])
        self.assertEqual(response['title'], "New Title")
        self.assertEqual(response['description'], "New Title")
        self.assertEqual(response['uuid'], lib['bundle_uuid'])
        self.assertEqual(response['num_blocks'], 0)
        self.assertEqual(response['version'], lib['version'])
        self.assertEqual(response['last_published'], None)
        self.assertEqual(response['has_unpublished_changes'], False)
        self.assertEqual(response['has_unpublished_deletes'], False)

        self._delete_library(lib['id'])
        with self.assertRaises(LibraryNotIndexedException):
            ContentLibraryIndexer.get_libraries([library_key])

    @override_settings(SEARCH_ENGINE="search.tests.mock_search_engine.MockSearchEngine")
    def test_update_library_blocks(self):
        """
        Test if indexes are updated when blocks in libraries are updated
        """
        def commit_library_and_verify(library_key):
            """
            Commit library changes, and verify that there are no uncommited changes anymore
            """
            last_published = ContentLibraryIndexer.get_libraries([library_key])[0]['last_published']
            self._commit_library_changes(str(library_key))
            response = ContentLibraryIndexer.get_libraries([library_key])[0]
            self.assertEqual(response['has_unpublished_changes'], False)
            self.assertEqual(response['has_unpublished_deletes'], False)
            self.assertGreaterEqual(response['last_published'], last_published)
            return response

        def verify_uncommitted_libraries(library_key, has_unpublished_changes, has_unpublished_deletes):
            """
            Verify uncommitted changes and deletes in the index
            """
            response = ContentLibraryIndexer.get_libraries([library_key])[0]
            self.assertEqual(response['has_unpublished_changes'], has_unpublished_changes)
            self.assertEqual(response['has_unpublished_deletes'], has_unpublished_deletes)
            return response

        lib = self._create_library(slug="test-lib-update-block", title="Title", description="Description")
        library_key = LibraryLocatorV2.from_string(lib['id'])

        # Verify uncommitted new blocks
        block = self._add_block_to_library(lib['id'], "problem", "problem1")
        response = verify_uncommitted_libraries(library_key, True, False)
        self.assertEqual(response['last_published'], None)
        self.assertEqual(response['num_blocks'], 1)
        # Verify committed new blocks
        self._commit_library_changes(lib['id'])
        response = verify_uncommitted_libraries(library_key, False, False)
        self.assertEqual(response['num_blocks'], 1)
        # Verify uncommitted deleted blocks
        self._delete_library_block(block['id'])
        response = verify_uncommitted_libraries(library_key, True, True)
        self.assertEqual(response['num_blocks'], 0)
        # Verify committed deleted blocks
        self._commit_library_changes(lib['id'])
        response = verify_uncommitted_libraries(library_key, False, False)
        self.assertEqual(response['num_blocks'], 0)

        block = self._add_block_to_library(lib['id'], "problem", "problem1")
        self._commit_library_changes(lib['id'])

        # Verify changes to blocks
        # Verify OLX updates on blocks
        self._set_library_block_olx(block["id"], "<problem/>")
        verify_uncommitted_libraries(library_key, True, False)
        commit_library_and_verify(library_key)
        # Verify asset updates on blocks
        self._set_library_block_asset(block["id"], "whatever.png", b"data")
        verify_uncommitted_libraries(library_key, True, False)
        commit_library_and_verify(library_key)
        self._delete_library_block_asset(block["id"], "whatever.png", expect_response=204)
        verify_uncommitted_libraries(library_key, True, False)
        commit_library_and_verify(library_key)

        lib2 = self._create_library(slug="test-lib-update-block-2", title="Title 2", description="Description")
        library_key2 = LibraryLocatorV2.from_string(lib2['id'])
        self._add_block_to_library(lib2["id"], "problem", "problem1")
        self._commit_library_changes(lib2["id"])

        #Verify new links on libraries
        self._link_to_library(lib["id"], "library_2", lib2["id"])
        verify_uncommitted_libraries(library_key, True, False)
        #Verify reverting uncommitted changes
        self._revert_library_changes(lib["id"])
        verify_uncommitted_libraries(library_key, False, False)
