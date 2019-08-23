/**
 * This is the publish XBlock modal implementation
 */
define(['underscore', 'gettext', 'edx-ui-toolkit/js/utils/string-utils',
  'js/views/modals/course_outline_modals/xblock_modal',
], function (
  _, gettext, StringUtils, CourseOutlineXBlockModal
) {
  'use strict';
  return CourseOutlineXBlockModal.extend({
    events: _.extend({}, CourseOutlineXBlockModal.prototype.events, {
      'click .action-publish': 'save'
    }),

    initialize: function () {
      CourseOutlineXBlockModal.prototype.initialize.call(this);
      if (this.options.xblockType) {
        this.options.modalName = 'bulkpublish-' + this.options.xblockType;
      }
    },

    getTitle: function () {
      return StringUtils.interpolate(
        gettext('Publish {display_name}'),
        {display_name: this.model.get('display_name')}
      );
    },

    getIntroductionMessage: function () {
      return StringUtils.interpolate(
        gettext('Publish all unpublished changes for this {item}?'),
        {item: this.options.xblockType}
      );
    },

    addActionButtons: function () {
      this.addActionButton('publish', gettext('Publish'), true);
      this.addActionButton('cancel', gettext('Cancel'));
    }
  });
});
