"""
Library Sourced Content XBlock
"""
import logging

from copy import copy
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Boolean, Scope, String
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xmodule.studio_editable import StudioEditableBlock as EditableChildrenMixin
from xmodule.validation import StudioValidation, StudioValidationMessage

log = logging.getLogger(__name__)

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
    source_block_id = String(
        display_name=_("Library Block"),
        help=_("Enter the IDs of the library XBlocks that you wish to use."),
        scope=Scope.content,
    )
    editable_fields = ("display_name", "source_block_id")
    has_children = True
    has_author_view = True

    def __str__(self):
        return "LibrarySourcedBlock: {}".format(self.display_name)

    def author_view(self, context):
        """
        Renders the Studio preview view.
        """
        fragment = Fragment()
        context = {} if not context else copy(context)  # Isolate context - without this there are weird bugs in Studio
        # EditableChildrenMixin.render_children will render HTML that allows instructors to make edits to the children
        self.render_children(context, fragment, can_reorder=False, can_add=False, can_move=False)
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

    def validate(self):
        """
        Validates the state of this library_sourced_xblock Instance. This is the override of the general XBlock method,
        and it will also ask its superclass to validate.
        """
        validation = super().validate()
        validation = StudioValidation.copy(validation)

        if not self.source_block_id:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.NOT_CONFIGURED,
                    "No XBlock has been configured for this component.",
                    action_class='edit-button',
                    action_label=_(u"Select XBlock.")
                )
            )
        return validation

    @XBlock.handler
    def submit_studio_edits(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Save changes to this block, applying edits made in Studio.
        """
        response = super().submit_studio_edits(*args, **kwargs)
        # Replace our current children with the latest ones from the libraries.
        lib_tools = self.runtime.service(self, 'library_tools')
        try:
            lib_tools.import_from_blockstore(self, self.source_block_id)
        except Exception as err:
            log.exception(err)
            raise JsonHandlerError(400, "Unable to save changes - are the Library Block IDs valid and readable?")
        return response
