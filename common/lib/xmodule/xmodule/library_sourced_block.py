"""
Library Sourced Content XBlock
"""
import logging

from copy import copy
from django.conf import settings
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String, List
from xblock.validation import ValidationMessage
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin
from webob import Response
from webpack_loader.templatetags.webpack_loader import render_bundle

from cms.lib.xblock.runtime import handler_url
from mako.template import Template as MakoTemplate
from xmodule.studio_editable import StudioEditableBlock as EditableChildrenMixin
from xmodule.validation import StudioValidation, StudioValidationMessage

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


@XBlock.wants('library_tools')  # Only needed in studio
class LibrarySourcedBlock(StudioEditableXBlockMixin, EditableChildrenMixin, XBlock):
    """
    Library Sourced Content XBlock

    Allows copying specific XBlocks from a Blockstore-based content library into
    a modulestore-based course. The selected blocks are copied and become
    children of this block.

    When we implement support for Blockstore-based courses, it's expected we'll
    use a different mechanism for importing library content into a course.
    """
    display_name = String(
        help=_("The display name for this component."),
        default="Library Sourced Content",
        display_name=_("Display Name"),
        scope=Scope.content,
    )
    source_block_ids = List(
        display_name=_("Library Block List"),
        help=_("Enter the IDs of the library XBlock that you wish to use."),
        scope=Scope.content,
    )
    editable_fields = ("display_name", "source_block_ids")
    has_children = True
    has_author_view = True
    resources_dir = 'assets/library_source_block'

    def __str__(self):
        return "LibrarySourcedBlock: {}".format(self.display_name)

    def studio_view(self, context):
        """
        Render a form for editing this XBlock
        """
        fragment = Fragment()
        render_bundle('LibrarySourcedBlockPicker')
        render_react = MakoTemplate(loader.load_unicode('../../../../common/djangoapps/pipeline_mako/templates/static_content.html'), default_filters=[]).get_def('renderReact')
        react_content = render_react.render(
            component="LibrarySourcedBlockPicker",
            id="library-sourced-block-picker",
            props={
                'saveUrl': handler_url(self, 'submit_studio_edits'),
                'selectedXblocks': self.source_block_ids,
            }
        )
        fragment.content = loader.render_django_template('templates/library-sourced-block-studio-view.html', {
            'react_content': react_content,
        })

        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/library_source_block.js'))
        fragment.initialize_js('LibrarySourceBlockAuthorView')

        return fragment

    def author_view(self, context):
        """
        Renders the Studio preview view.
        """
        fragment = Fragment()
        # TODO: Show studio view here if no IDs are set
        context = {} if not context else copy(context)  # Isolate context - without this there are weird bugs in Studio
        # EditableChildrenMixin.render_children will render HTML that allows instructors to make edits to the children
        context['can_move'] = False
        self.render_children(context, fragment, can_reorder=False, can_add=False)
        return fragment

    def student_view(self, context):
        """
        Renders the view that learners see.
        """
        result = Fragment()
        child_frags = self.runtime.render_children(self, context=context)
        result.add_resources(child_frags)
        result.add_content('<div class="library-sourced-content">')
        for frag in child_frags:
            result.add_content(frag.content)
        result.add_content('</div>')
        return result

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data. Instead of checking fields like self.name, check the
        fields set on data, e.g. data.name. This allows the same validation method to be re-used
        for the studio editor. Any errors found should be added to "validation".
        This method should not return any value or raise any exceptions.
        All of this XBlock's fields should be found in "data", even if they aren't being changed
        or aren't even set (i.e. are defaults).
        """
        if len(data.source_block_ids) > 10:
            validation.add(ValidationMessage(ValidationMessage.ERROR, "A maximum of 10 components may be added."))


    @XBlock.handler
    def submit_studio_edits(self, *args, **kwargs):
        """
        Save changes to this block, applying edits made in Studio.
        """
        response = super().submit_studio_edits(*args, **kwargs)
        # Replace our current children with the latest ones from the libraries.
        lib_tools = self.runtime.service(self, 'library_tools')
        try:
            lib_tools.import_from_blockstore(self, self.source_block_ids)
        except Exception as err:  # pylint: disable=broad-except
            log.exception(err)
            return Response(_(u"Importing Library Block failed - are the IDs valid and readable?"), status=400)
        return response
